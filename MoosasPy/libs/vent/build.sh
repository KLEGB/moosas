#!/usr/bin/env bash
set -euo pipefail

go build -o MoosasAFN MoosasAFN.go
go build -o ./afn/afn afn.go
go build -o ./mkdir/mkdir ./mkdir/mkdir.go
go build -o ./triangulate/triangulate ./triangulate/triangulate.go
