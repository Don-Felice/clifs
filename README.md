![Lint](https://github.com/Don-Felice/clifs/workflows/Lint/badge.svg)
![Test](https://github.com/Don-Felice/clifs/workflows/Test/badge.svg)

# clifs

Command line interface for basic file system operations.

For installation run:

```powershell
pip install clifs
```

After installation all functionality can be accessed typing `clifs` in the command line, which alone will show a list of installed plugins.

To implement your own plugin best inherit from the `clifs.ClifsPlugin` class.

# Plugins installed by default:

## Rename (`ren`)

Rename files or directories using regular expressions. Supports options such as selecting files and folders by sub-string filter or list. Type `clifs ren --help` for a list of options. By default a preview mode is running to prevent unpleasant surprises.

### Example:

Command:

```powershell
clifs ren ".\some_dir" --recursive --pattern "(^suffix)\.(.*)" --replacement "\1_suffix.\2"
```

Output:

<img src="https://github.com/Don-Felice/clifs/raw/v1.2.1/doc/imgs/example_ren.png" width="800"/>

## Disc Usage (`du`)

Show disc usage for one or more directories.

### Example:

Command:

```powershell
clifs du "some\dir\on\some_drive" "some\other\dir\on\some_other_drive" "some\other\dir\on\yet_another_drive"
```

Output:

<img src="https://github.com/Don-Felice/clifs/raw/v1.2.1/doc/imgs/example_du.png" width="800"/>

## Directory Tree (`tree`)

Show a directory tree including sizes of folders and files. Supports options such as controlling the tree depth or showing folders only. Type `clifs tree --help` for a list of options.

### Example:

Command:

```powershell
clifs tree .\clifs --depth 2
```

Output:

<img src="https://github.com/Don-Felice/clifs/raw/v1.2.1/doc/imgs/example_tree.png" width="800"/>

## Copy (`cp`)

Copy files from one location to the other.
Supports options such as selecting files by sub-string filter or list, or flattening the folder hierarchy. Type `clifs cp --help` for a full list of options.

### Example:

Command:

```powershell
clifs cp ".\some_source_dir" ".\some_dest_dir" --recursive --flatten --keep_all
```

Output:

<img src="https://github.com/Don-Felice/clifs/raw/v1.2.1/doc/imgs/example_cp.png" width="800"/>

## Move (`mv`)

Move files from one location to the other.
Supports options such as selecting files by sub-string filter or list, or flattening the folder hierarchy. Type `clifs mv --help` for a full list of options.

### Example:

Command:

```powershell
clifs mv ".\some_source_dir" ".\some_dest_dir" --recursive --skip_existing
```

Output:
<img src="https://github.com/Don-Felice/clifs/raw/v1.2.1/doc/imgs/example_mv.png" width="800"/>

## Delete (`del`)

Delete files from the drive.
Supports options such as selecting files by sub-string filter or list. Type `clifs del --help` for a full list of options.

### Example:

Command:

```powershell
clifs del ".\some_dir" --recursive --filterstring ".py"
```

Output:

<img src="https://github.com/Don-Felice/clifs/raw/v1.2.1/doc/imgs/example_del.png" width="800"/>

## Backup (`backup`)

Back up files and folders. Supports backing up via a config file giving multiple source/target pairs and the option to delete files which are not present in the source directory from the corresponding target directory.
Type `clifs backup --help` for a full list of options.

### Example:

Command:

```powershell
clifs backup --dir_source ".\some_source_dir" --dir_dest ".\some_dest_dir" --delete --verbose
```

Output:

<img src="https://github.com/Don-Felice/clifs/raw/v1.2.1/doc/imgs/example_backup.png" width="800"/>
