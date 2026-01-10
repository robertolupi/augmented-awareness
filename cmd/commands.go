package cmd

import (
	"fmt"
	"journal/internal/application"
	"journal/internal/config"
	"log"
	"os"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var (
	vaultPath      string
	journalSection string
	dataPath       string

	app *application.App

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
	cobra.OnInitialize(initApp)

	rootCmd.PersistentFlags().StringVar(&vaultPath, "vault", "", "Path to the Obsidian vault")
	rootCmd.PersistentFlags().StringVar(&journalSection, "section", "", "Section of the journal entry")
	rootCmd.PersistentFlags().StringVar(&dataPath, "data", "", "Path to the data directory")

	err := viper.BindPFlag(config.VaultPath, rootCmd.PersistentFlags().Lookup("vault"))
	if err != nil {
		log.Fatalln(err)
	}
	err = viper.BindPFlag(config.JournalSection, rootCmd.PersistentFlags().Lookup("section"))
	if err != nil {
		log.Fatalln(err)
	}

	err = viper.BindPFlag(config.DataPath, rootCmd.PersistentFlags().Lookup("data"))
	if err != nil {
		log.Fatalln(err)
	}

	initRecordCmd()
	initStopCmd()
	initBusyCmd()
	initListCmd()
	initAmendCmd()
	initUiCmd()
	initMcpCmd()
	initTasksCmd()
	initSearchCmd()
	initIndexCmd()
	initTasksCleanupCmd()
	initPomodoroCmd()
}

func initApp() {
	if err := config.InitConfig(""); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
	vaultPath = viper.GetString(config.VaultPath)
	journalSection = viper.GetString(config.JournalSection)
	dataPath = viper.GetString(config.DataPath)

	var err error
	app, err = application.New(vaultPath, journalSection, dataPath)
	if err != nil {
		log.Fatalf("Failed to create application: %v", err)
	}
}
