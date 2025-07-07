package cmd

import (
	"github.com/spf13/cobra"
	"journal/internal/obsidian"
	"time"
)

var (
	vaultPath      string
	journalSection string
	vault          *obsidian.Vault

	rootCmd = &cobra.Command{
		Use:   "journal",
		Short: "Update my journal in Obsidian",
		Long:  `A simple command line tool to update my journal in Obsidian.`,
	}
)

func Execute() error {
	return rootCmd.Execute()
}

func init() {
	rootCmd.PersistentFlags().StringVar(&vaultPath, "vault", "~/data/notes", "Path to the Obsidian vault")
	rootCmd.PersistentFlags().StringVar(&journalSection, "section", "Journal and events", "Section of the journal entry")

	initRecordCmd()
	initBusyCmd()
	initListCmd()
	initAmendCmd()
	initUiCmd()
	initMcpCmd()
	initTasksCmd()
	initSearchCmd()
}

func initVault() error {
	var err error
	vault, err = obsidian.NewVault(vaultPath)
	if err != nil {
		return err
	}
	return nil
}

func today() string {
	return obsidian.DateToPage(time.Now())
}

func oneMonthAgo() string {
	return obsidian.DateToPage(time.Now().AddDate(0, -1, 0))
}

func sixDaysAgo() string {
	return obsidian.DateToPage(time.Now().AddDate(0, 0, -6))
}
