package cmd

import (
	"encoding/json"
	"fmt"
	"journal/internal/datetime"
	"journal/internal/obsidian"
	"net/http"
	"strings"
	"time"

	"github.com/spf13/cobra"
)

const (
	// Transitions
	idleToWork  = "idle_to_work"
	workToIdle  = "work_to_idle"
	workToBreak = "work_to_break"
	breakToIdle = "break_to_idle"
)

type Payload struct {
	StartTime  uint64 `json:"start_time"`
	EventTime  uint64 `json:"event_time"`
	Transition string `json:"transition"`
	WorkFlavor string `json:"work_flavor"`
}

func (p *Payload) ToPomodoro() *Pomodoro {
	var endTime time.Time
	if p.Transition == workToIdle || p.Transition == workToBreak {
		endTime = time.Unix(int64(p.EventTime), 0)
	}
	return &Pomodoro{
		StartTime: time.Unix(int64(p.StartTime), 0),
		EndTime:   endTime,
		Flavor:    p.WorkFlavor,
	}
}

type Pomodoro struct {
	StartTime time.Time
	EndTime   time.Time
	Flavor    string
}

func (p *Pomodoro) ToDateAndEvent() (datetime.Date, *obsidian.Event) {
	var startTime = datetime.Time(p.StartTime.Format("15:04"))
	var endTime datetime.Time = datetime.EmptyTime
	if !p.EndTime.IsZero() {
		endTime = datetime.Time(p.EndTime.Format("15:04"))
	}
	return datetime.Date(p.StartTime.Format("2006-01-02")), &obsidian.Event{
		StartTime: startTime,
		EndTime:   endTime,
		Text:      fmt.Sprintf("Pomodoro #%s", p.Flavor),
		Tags:      []string{p.Flavor},
	}
}

var (
	pomodoroPort string
	pomodoroCmd  = &cobra.Command{
		Use:   "pomodoro",
		Short: "Receive pomodoro timer notifications",
		RunE: func(cmd *cobra.Command, args []string) error {
			// Start a HTTP server that listens on the specified port
			// and receives notifications from the pomodoro timer.

			// Handle POST requests to //pomodoros/{id}/transitions with JSON body
			// containing the transition data.

			// For now, we will just print the transition data to the console.
			http.HandleFunc("/pomodoros/{id}/transitions", func(w http.ResponseWriter, r *http.Request) {
				if r.Method != "POST" {
					w.WriteHeader(http.StatusMethodNotAllowed)
					return
				}

				// extract transition id
				id := strings.Split(r.URL.Path, "/")[2]
				// Decode JSON body
				var data Payload
				err := json.NewDecoder(r.Body).Decode(&data)
				if err != nil {
					w.WriteHeader(http.StatusBadRequest)
					fmt.Println("Error decoding JSON:", err)
					return
				}

				date, event := data.ToPomodoro().ToDateAndEvent()

				fmt.Println("Received pomodoro transition for id:", id)
				fmt.Printf("Date: %s\n", date)
				fmt.Printf("Event: %+v\n", event)

				if data.Transition == idleToWork || data.Transition == breakToIdle {
					w.WriteHeader(http.StatusOK)
					return
				}

				page, err := app.Vault.Page(date.String())
				if err != nil {
					w.WriteHeader(http.StatusInternalServerError)
					fmt.Println("Error getting page:", err)
					return
				}

				section, err := page.FindSection(journalSection)
				if err != nil {
					w.WriteHeader(http.StatusInternalServerError)
					fmt.Println("Error finding section:", err)
					return
				}

				if err := section.AddEvent(*event); err != nil {
					w.WriteHeader(http.StatusInternalServerError)
					fmt.Println("Error adding event:", err)
					return
				}

				if err := page.Save(); err != nil {
					w.WriteHeader(http.StatusInternalServerError)
					fmt.Println("Error saving page:", err)
					return
				}
			})

			fmt.Println("Listening on port :" + pomodoroPort)
			http.ListenAndServe(":"+pomodoroPort, nil)

			return nil
		},
	}
)

func initPomodoroCmd() {
	rootCmd.AddCommand(pomodoroCmd)

	pomodoroCmd.Flags().StringVarP(&pomodoroPort, "port", "p", "8080", "Port to listen on")
}
