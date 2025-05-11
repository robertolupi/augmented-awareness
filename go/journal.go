package main

import "journal/cmd"

func main() {
	if err := cmd.Execute(); err != nil {
		panic(err)
	}
}
