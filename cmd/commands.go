package cmd

import (
	"fmt"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	"journal/internal/config"
	"journal/internal/obsidian"
	"log"
	"os"
	"time"
)

var (
	vaultPath      string
	journalSection string
	dataPath       string
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
	cobra.OnInitialize(initConfig)

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
	initBusyCmd()
	initListCmd()
	initAmendCmd()
	initUiCmd()
	initMcpCmd()
	initTasksCmd()
	initSearchCmd()
	initIndexCmd()
}

func initConfig() {
	if err := config.InitConfig(""); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
	vaultPath = viper.GetString(config.VaultPath)
	journalSection = viper.GetString(config.JournalSection)
	dataPath = viper.GetString(config.DataPath)

	var err error
	vault, err = obsidian.NewVault(vaultPath)
	if err != nil {
		log.Fatalf("Error initializing vault: %v", err)
	}
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
