# mapnik-lost-manual

An attempt to create a Mapnik manual as a single, self contained document

For public document versions see http://get-map.org/mapnik-lost-manual/

## Requirements

* Mapnik Python Bindings
* AsciiDoctor
* AsciiDoctor PDF backend
* AsciiDoctor Multipage backend
* AsciiDoctor Epub3 Backend
* GNU Make
* rsync (for upload to public server)
* codespell (for the pre-commit spelling check)

### On Debian

```
apt-get install make rsync python3-mapnik asciidoctor codespell
gem install asciidoctor-pdf asciidoctor-multipage asciidoctor-epub3
```
