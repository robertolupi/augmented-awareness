package application

import (
	"github.com/stretchr/testify/assert"
	"testing"
	"time"
)

const goldenBusyReport = `Busy report from 2025-03-30 to 2025-04-01:
                                   Total	▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁██▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁         1h0m0s  100.00%
                                 No tags	▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁             0s  0.00%
                                    work	▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁██▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁         1h0m0s  100.00%
                                     aww	▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁             0s  0.00%
`

func TestApp_BusyReport(t *testing.T) {
	app := AppForTesting(t)

	report, err := app.BusyReport("2025-03-30", "2025-04-01", true, 30*time.Minute)
	if err != nil {
		t.Fatalf("Failed to generate busy report: %v", err)
	}

	assert.Equal(t, goldenBusyReport, report, "Busy report does not match expected output")
}
