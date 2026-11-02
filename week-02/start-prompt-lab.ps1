# Serves the Prompt Lab at http://localhost:8562/ and saves its exports as .md files in the runs folder.
# Run it with start-prompt-lab.bat. Close the window (or press Ctrl+C) to stop.
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$runs = Join-Path $root "runs"
$port = 8562
$origin = "http://localhost:$port"

$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("$origin/")
$listener.Start()
Write-Host "Prompt Lab running at $origin/  (close this window to stop)"
New-Item -ItemType Directory -Force $runs | Out-Null
Write-Host "Exports are saved to $runs"
Start-Process "$origin/prompt-lab.html"

try {
  while ($listener.IsListening) {
    $task = $listener.GetContextAsync()
    while (-not $task.AsyncWaitHandle.WaitOne(500)) {}  # wait in short steps so Ctrl+C works
    $ctx = $task.GetAwaiter().GetResult()
    $req = $ctx.Request
    $res = $ctx.Response
    try {
      $path = $req.Url.AbsolutePath
      if ($req.HttpMethod -eq "GET" -and ($path -eq "/" -or $path -eq "/prompt-lab.html")) {
        $bytes = [IO.File]::ReadAllBytes((Join-Path $root "prompt-lab.html"))
        $res.ContentType = "text/html; charset=utf-8"
        $res.OutputStream.Write($bytes, 0, $bytes.Length)
      }
      elseif ($req.HttpMethod -eq "POST" -and $path -eq "/export") {
        if ($req.Headers["Origin"] -ne $origin) {
          $res.StatusCode = 403  # only this page may save files
        }
        else {
          # Next free name: task-01.md, task-02.md, ... so earlier exports are never overwritten.
          $n = 1
          while (Test-Path (Join-Path $runs ("task-{0:D2}.md" -f $n))) { $n++ }
          $name = "task-{0:D2}.md" -f $n
          $reader = New-Object IO.StreamReader($req.InputStream, [Text.Encoding]::UTF8)
          $md = $reader.ReadToEnd()
          [IO.File]::WriteAllText((Join-Path $runs $name), $md, (New-Object Text.UTF8Encoding $false))
          Write-Host "Saved runs\$name"
          $bytes = [Text.Encoding]::UTF8.GetBytes($name)
          $res.ContentType = "text/plain; charset=utf-8"
          $res.OutputStream.Write($bytes, 0, $bytes.Length)
        }
      }
      else {
        $res.StatusCode = 404
      }
    }
    catch {
      $res.StatusCode = 500
      Write-Host "Error: $($_.Exception.Message)"
    }
    finally {
      $res.Close()
    }
  }
}
finally {
  $listener.Stop()
}
