#!/usr/bin/env bash
set -euo pipefail

go build -o MoosasEnergy MoosasEnergy.go
go build -o MoosasEnergyResidential MoosasEnergyResidential.go
go build -o MoosasEnergyPublic MoosasEnergyPublic.go
