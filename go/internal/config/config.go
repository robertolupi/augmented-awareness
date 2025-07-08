package config

import (
	"github.com/mitchellh/go-homedir"
	"github.com/spf13/viper"
	"strings"
)

const (
	VaultPath      = "vault.path"
	JournalSection = "journal.section"
	DataPath       = "data.path"
)

func InitConfig(configFile string) error {
	viper.SetDefault(VaultPath, "~/data/notes")
	viper.SetDefault(JournalSection, "Journal and events")
	viper.SetDefault(DataPath, "~/journal")

	if configFile != "" {
		viper.SetConfigFile(configFile)
	} else {
		home, err := homedir.Dir()
		if err != nil {
			return err
		}
		viper.AddConfigPath(home)
		viper.SetConfigName(".journal")
		viper.SetConfigType("yaml")
	}

	viper.SetEnvPrefix("JOURNAL")
	viper.SetEnvKeyReplacer(strings.NewReplacer(".", "_"))
	viper.AutomaticEnv()

	err := viper.ReadInConfig()
	if _, ok := err.(viper.ConfigFileNotFoundError); ok {
		// Config file not found; ignore error
	} else if err != nil {
		return err
	}

	return nil
}
