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

type Activity struct {
	Description string `json:"description"`
	StartTime   int64  `json:"startTime"` // Milliseconds
	EndTime     *int64 `json:"endTime"`   // Milliseconds
	Tags        string `json:"tags"`
}

func (a *Activity) ToDateAndEvent() (datetime.Date, *obsidian.Event) {
	var startTime = time.Unix(0, a.StartTime*int64(time.Millisecond))
	var endTime time.Time
	if a.EndTime != nil {
		endTime = time.Unix(0, *a.EndTime*int64(time.Millisecond))
	}
	var endtime2 datetime.Time = datetime.EmptyTime
	if !endTime.IsZero() {
		endtime2 = datetime.Time(endTime.Format("15:04"))
	}

	tags := strings.Split(a.Tags, ",")
	for i, tag := range tags {
		tags[i] = "#" + tag
	}

	return datetime.Date(startTime.Format("2006-01-02")), &obsidian.Event{
		StartTime: datetime.Time(startTime.Format("15:04")),
		EndTime:   endtime2,
		Text:      fmt.Sprintf("%s %s", a.Description, strings.Join(tags, " ")),
		Tags:      tags,
	}
}

type Pomodoro struct {
	StartTime  uint64 `json:"start_time"`
	EventTime  uint64 `json:"event_time"`
	Transition string `json:"transition"`
	WorkFlavor string `json:"work_flavor"`
}

func (p *Pomodoro) ToDateAndEvent() (datetime.Date, *obsidian.Event) {
	var startTime = time.Unix(int64(p.StartTime), 0)
	var endTime time.Time
	if p.Transition == workToIdle || p.Transition == workToBreak {
		endTime = time.Unix(int64(p.EventTime), 0)
	}

	var endtime2 datetime.Time = datetime.EmptyTime
	if !endTime.IsZero() {
		endtime2 = datetime.Time(endTime.Format("15:04"))
	}
	return datetime.Date(startTime.Format("2006-01-02")), &obsidian.Event{
		StartTime: datetime.Time(startTime.Format("15:04")),
		EndTime:   endtime2,
		Text:      fmt.Sprintf("Pomodoro #%s", p.WorkFlavor),
		Tags:      []string{p.WorkFlavor},
	}
}

func saveEvent(date datetime.Date, event *obsidian.Event) error {
	page, err := app.Vault.Page(date.String())
	if err != nil {
		return err
	}

	section, err := page.FindSection(journalSection)
	if err != nil {
		return err
	}

	if err := section.AddEvent(*event); err != nil {
		return err
	}

	if err := page.Save(); err != nil {
		return err
	}

	return nil
}

func handlePomodoroTransition(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		w.WriteHeader(http.StatusMethodNotAllowed)
		return
	}

	// extract transition id
	id := strings.Split(r.URL.Path, "/")[2]
	// Decode JSON body
	var data Pomodoro
	err := json.NewDecoder(r.Body).Decode(&data)
	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		fmt.Println("Error decoding JSON:", err)
		return
	}

	date, event := data.ToDateAndEvent()

	fmt.Println("Received pomodoro transition for id:", id)
	fmt.Printf("Date: %s\n", date)
	fmt.Printf("Event: %+v\n", event)

	if data.Transition == idleToWork || data.Transition == breakToIdle {
		w.WriteHeader(http.StatusOK)
		return
	}

	err = saveEvent(date, event)
	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		fmt.Println("Error saving event:", err)
		return
	}
}

func handleActivities(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		w.WriteHeader(http.StatusMethodNotAllowed)
		return
	}

	// Decode JSON body
	var data []Activity
	err := json.NewDecoder(r.Body).Decode(&data)
	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		fmt.Println("Error decoding JSON:", err)
		return
	}

	for n, activity := range data {
		date, event := activity.ToDateAndEvent()

		fmt.Printf("Received Activity %d\n", n+1)
		fmt.Printf("Date: %s\n", date)
		fmt.Printf("Event: %+v\n", event)

		err := saveEvent(date, event)
		if err != nil {
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Println("Error saving event:", err)
			return
		}
	}

	w.WriteHeader(http.StatusOK)
}

var (
	pomodoroPort string
	pomodoroCmd  = &cobra.Command{
		Use:   "pomodoro",
		Short: "Receive pomodoro timer notifications",
		RunE: func(cmd *cobra.Command, args []string) error {
			http.HandleFunc("/pomodoros/{id}/transitions", handlePomodoroTransition)
			http.HandleFunc("/activities", handleActivities)

			fmt.Println("Listening on port :" + pomodoroPort)
			err := http.ListenAndServe(":"+pomodoroPort, nil)
			if err != nil {
				fmt.Println("ListenAndServe error:", err)
			}

			return nil
		},
	}
)

func initPomodoroCmd() {
	rootCmd.AddCommand(pomodoroCmd)

	pomodoroCmd.Flags().StringVarP(&pomodoroPort, "port", "p", "8080", "Port to listen on")
}
