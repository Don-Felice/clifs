# clifs Changelog

## Unreleased Changes 


## v1.0.0 - Nov. 17, 2023

- more concise naming of cli arguments
- more concise reporting
- documentation of plugin feature and included plugins in the README.md
- make `clifs.ClifsPlugin` directly importable from top level

## v0.5.1 - Oct. 15, 2023

- update pylint to v3.0.1
- CI:
  - add more thorough checks on release requirements to release pipeline
  - run testing and linting via Hatch
  - update version of checkout and setup-python actions

## v0.5.0 - Oct. 13, 2023

- Some refactoring:
  - use Counter class for all counters
  - use Enum class for storage of color constants
  - some other minor refactors

## v0.4.2 - Oct. 13, 2023

- add CI release pipeline
- add CHANGELOG.md
