![Lint](https://github.com/Don-Felice/clifs/workflows/Lint/badge.svg)
![Test](https://github.com/Don-Felice/clifs/workflows/Test/badge.svg)

# clifs

Multi-platform command line interface for file system operations.

For installation run:

```powershell
pip install clifs
```

After installation all functionality can be accessed typing `clifs` in the command line, which alone will show a list of installed plugins.

To implement your own plugin best inherit from the `clifs.ClifsPlugin` class.

# Plugins installed by default:

## Rename (`ren`)

Rename files or directories using regular expressions. Supports options such as selecting files and folders by sub-string filter, time of the last modification or creation/change, or by list. Type `clifs ren --help` for a list of options. By default a preview mode is running to prevent unpleasant surprises.

### Example:

Command:

```powershell
clifs ren ".\some_dir" --recursive --pattern "(?<!_suffix)\.(.*)" --replacement "_suffix.\1"
```

Output:

<img src="https://github.com/Don-Felice/clifs/raw/v1.5.1/doc/imgs/example_ren.png" width="800"/>

## Disc Usage (`du`)

Show disc usage for one or more directories.

### Example:

Command:

```powershell
clifs du "some\dir\on\some_drive" "some\other\dir\on\some_other_drive" "some\other\dir\on\yet_another_drive"
```

Output:

<img src="https://github.com/Don-Felice/clifs/raw/v1.5.1/doc/imgs/example_du.png" width="800"/>

## Directory Tree (`tree`)

Show a directory tree including sizes of folders and files. Supports options such as controlling the tree depth or showing folders only. Type `clifs tree --help` for a list of options.

### Example:

Command:

```powershell
clifs tree .\clifs --depth 2
```

Output:

<img src="https://github.com/Don-Felice/clifs/raw/v1.5.1/doc/imgs/example_tree.png" width="800"/>

## Streaming Editor (`sed`)

Edit text files using regular expressions. Runs line by line and gives a preview of the changes by default. Supports options such as picking lines by number, selection of files by sub-string filter, time of the last modification or creation/change, or by list. Type `clifs sed --help` for a list of options.

You can e.g. remove specific lines choosing `-pt ".*[\r\n]+" -l 5` or add lines in specific locations using `-pt "[\r\n]+" -rp "\nadded line\n" -l 3,4"`.

### Example:

```powershell
clifs sed ".\some\place" --pattern "(s\w*)" --replacement "no \1"  --lines 4-6 --recursive
```

Output:

<img src="https://github.com/Don-Felice/clifs/raw/v1.5.1/doc/imgs/example_sed.png" width="800"/>

## Copy (`cp`)

Copy files from one location to the other.
Supports selection of files and folders by sub-string filter, time of the last modification or creation/change, or by list. Also supports flattening the folder hierarchy. Type `clifs cp --help` for a full list of options.

### Example:

Command:

```powershell
clifs cp ".\some_source_dir" ".\some_dest_dir" --recursive --flatten --keep_all
```

Output:

<img src="https://github.com/Don-Felice/clifs/raw/v1.5.1/doc/imgs/example_cp.png" width="800"/>

## Move (`mv`)

Move files from one location to the other.
Supports selection of files and folders by sub-string filter, time of the last modification or creation/change, or by list. Also supports flattening the folder hierarchy. Type `clifs mv --help` for a full list of options.

### Example:

Command:

```powershell
clifs mv ".\some_source_dir" ".\some_dest_dir" --recursive --skip_existing
```

Output:
<img src="https://github.com/Don-Felice/clifs/raw/v1.5.1/doc/imgs/example_mv.png" width="800"/>

## Delete (`del`)

Delete files from the drive.
Supports options such as selecting files and folders by sub-string filter, time of the last modification or creation/change, or by list. Type `clifs del --help` for a full list of options.

### Example:

Command:

```powershell
clifs del ".\some_dir" --recursive --filterstring ".py"
```

Output:

<img src="https://github.com/Don-Felice/clifs/raw/v1.5.1/doc/imgs/example_del.png" width="800"/>

## Backup (`backup`)

Back up files and folders. Supports backing up via a config file giving multiple source/target pairs and the option to delete files which are not present in the source directory from the corresponding target directory.
Type `clifs backup --help` for a full list of options.

### Example:

Command:

```powershell
clifs backup --dir_source ".\some_source_dir" --dir_dest ".\some_dest_dir" --delete --verbose
```

Output:

<img src="https://github.com/Don-Felice/clifs/raw/v1.5.1/doc/imgs/example_backup.png" width="800"/>
