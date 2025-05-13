package cmd

import (
	"fmt"
	"github.com/spf13/cobra"
	"journal/internal/obsidian"
	"log"
	"sort"
	"strings"
	"time"
)

var (
	busyStartDate  string
	busyEndDate    string
	busyExpandTags bool

	busyCmd = &cobra.Command{
		Use:   "busy",
		Short: "Show how I spent my time",
		Long:  `Show how I spent my time in the last week.`,
		Run: func(cmd *cobra.Command, args []string) {
			if err := initVault(); err != nil {
				log.Fatalf("Failed to initialize vault: %v", err)
			}

			var dateRange []string
			if busyStartDate != "" && busyEndDate != "" {
				start, err := time.Parse("2006-01-02", busyStartDate)
				if err != nil {
					log.Fatalf("Failed to parse start date: %v", err)
				}
				end, err := time.Parse("2006-01-02", busyEndDate)
				if err != nil {
					log.Fatalf("Failed to parse end date: %v", err)
				}

				for d := start; d.Before(end) || d.Equal(end); d = d.AddDate(0, 0, 1) {
					dateRange = append(dateRange, d.Format("2006-01-02"))
				}
			}

			var pages []*obsidian.Page
			for _, date := range dateRange {
				page, err := vault.Page(date)
				if err != nil {
					log.Printf("Failed to get journal page for %s: %v", date, err)
				}
				pages = append(pages, page)
			}
			fmt.Printf("Found %d journal pages\n", len(pages))

			tagsByDuration := make(map[string]time.Duration)
			var totalDuration time.Duration

			for _, page := range pages {

				section, err := page.FindSection(journalSection)
				if err != nil {
					log.Printf("Failed to find section %s in journal page: %v", journalSection, err)
					continue
				}

				for i := section.Start; i < section.End; i++ {
					add := true
					event := obsidian.MaybeParseEvent(page.Content[i])
					if event != nil {
						for _, tag := range event.Tags {
							if tag == "" {
								continue
							}
							if _, ok := tagsByDuration[tag]; !ok {
								tagsByDuration[tag] = 0
							}
							tagsByDuration[tag] += event.Duration
							if add {
								totalDuration += event.Duration
								add = false
							}
						}
					}
				}
			}

			if busyExpandTags {
				tagsByDuration = expandTags(tagsByDuration)
			}

			// Sort tags by duration in descending order by duration
			type tagDuration struct {
				Tag      string
				Duration time.Duration
				Percent  float64
			}
			var tagDurations []tagDuration
			for tag, duration := range tagsByDuration {
				tagDurations = append(tagDurations, tagDuration{Tag: tag, Duration: duration})
			}
			for i := range tagDurations {
				tagDurations[i].Percent = float64(tagDurations[i].Duration) / float64(totalDuration) * 100
			}
			sort.Slice(tagDurations, func(i, j int) bool {
				return tagDurations[i].Duration > tagDurations[j].Duration
			})

			fmt.Println("Tags sorted by duration:")
			for _, tagDuration := range tagDurations {
				fmt.Printf("%40s\t%14s  %.2f%%\n", tagDuration.Tag, tagDuration.Duration, tagDuration.Percent)
			}
		},
	}
)

func expandTags(tagsByDuration map[string]time.Duration) map[string]time.Duration {
	var seen = make(map[string]int)
	var expandedTagsByDuration = make(map[string]time.Duration)
	for tag, duration := range tagsByDuration {
		seen[tag] = 2 // 2 or higher means we always show this tag
		parts := strings.Split(tag, "/")
		for i := 1; i <= len(parts); i++ {
			prefix := strings.Join(parts[:i], "/")
			if _, ok := expandedTagsByDuration[prefix]; !ok {
				expandedTagsByDuration[prefix] = 0
			}
			if _, ok := seen[prefix]; !ok {
				seen[prefix] = 0
			}
			seen[prefix]++
			expandedTagsByDuration[prefix] += duration
		}
	}
	result := make(map[string]time.Duration)
	for tag, duration := range expandedTagsByDuration {
		if seen[tag] > 1 {
			tagsByDuration[tag] = duration
		}
	}
	return result
}

func initBusyCmd() {
	rootCmd.AddCommand(busyCmd)

	busyCmd.Flags().StringVar(&busyStartDate, "start", oneWeekAgo(), "Start date (YYYY-MM-DD)")
	busyCmd.Flags().StringVar(&busyEndDate, "end", today(), "End date (YYYY-MM-DD)")
	busyCmd.Flags().BoolVarP(&busyExpandTags, "expand-tags", "e", false, "Expand tags to show all sub-tags")
}
