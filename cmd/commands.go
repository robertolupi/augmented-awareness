package cmd

import (
	"fmt"
	"journal/internal/application"
	"journal/internal/config"
	"log"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var (
	vaultPath      string
	journalSection string
	dataPath       string

	app *application.App

	rootCmd = &cobra.Command{
		Use:           "journal",
		Short:         "Update my journal in Obsidian",
		Long:          `A simple command line tool to update my journal in Obsidian.`,
		SilenceErrors: true,
		SilenceUsage:  true,
	}
)

func Execute() error {
	return rootCmd.Execute()
}

func init() {
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

	rootCmd.PersistentPreRunE = func(cmd *cobra.Command, args []string) error {
		return initApp()
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

func initApp() error {
	if err := config.InitConfig(""); err != nil {
		return fmt.Errorf("load config: %w", err)
	}
	vaultPath = viper.GetString(config.VaultPath)
	journalSection = viper.GetString(config.JournalSection)
	dataPath = viper.GetString(config.DataPath)

	var err error
	app, err = application.New(vaultPath, journalSection, dataPath)
	if err != nil {
		return fmt.Errorf("create application: %w", err)
	}
	return nil
}
