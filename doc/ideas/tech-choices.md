# Technological choices

## Programming Languages

- The core system is implemented in **Python**, for fast prototyping and components that are not performance critical.
- Rust is an option for future components, if Python performace is not enough.
- Porting to Julia is a poossible alternative, if Python performance is not enough.
- Go or Rust can be used for system programming, if needed.
- Electron, TypeScript/React-Native, or Kotlin are options for mobile development, or crossplatform desktop development.
- IoT components are developed in C++, using PlatformIO as the build system.

## Target Operating systems

- Agents should run on Linux, MacOS, Windows
- Servers should run on Linux and MacOS
- Mobile components should run on Android, possibly iOS if needed

## Data Storage and formats

- Apache Arrow for data intercharge
- Apache Parquet for data storage, local data lake
- SQLite or DuckDB for metadata storage and querying

## Protocols

- REST
- MQTTv5
- gRPC, FlightRPC
