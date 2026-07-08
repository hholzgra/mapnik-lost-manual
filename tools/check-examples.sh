#! /bin/bash
# Verify that example map styles still load and render.
#
# Called with a list of example XML files (as the pre-commit hook does);
# with no arguments it checks every example except those under disabled/.
#
# Examples whose .png and .svg are newer than the .xml are skipped;
# use -f to re-render regardless (e.g. after a mapnik upgrade).
set -u

cd "$(dirname "$0")/.." || exit 1

force=0
if [ "${1:-}" = "-f" ]
then
	force=1
	shift
fi

if [ ! -e examples/data/ne_110m_admin_0_countries_lakes.shp ] \
|| [ ! -e examples/data/ne_50m_graticules_30.shp ]
then
	echo "Natural Earth shapefiles missing, fetching them via 'make shapefiles'"
	make -s shapefiles || exit 1
fi

if [ $# -eq 0 ]
then
	set -- $(find examples -name '*.xml' -not -path '*/disabled/*' | sort)
fi

failed=()

for xml in "$@"
do
	case "$xml" in
		*/disabled/*) continue ;;
	esac
	base=${xml%.xml}
	if [ $force -eq 0 ] && [ "$base.png" -nt "$xml" ] && [ "$base.svg" -nt "$xml" ]
	then
		continue
	fi
	echo "  $xml"
	if ! examples/render.sh "$xml"
	then
		failed+=("$xml")
	fi
done

if [ ${#failed[@]} -gt 0 ]
then
	echo
	echo "Failed to render:"
	printf '  %s\n' "${failed[@]}"
	exit 1
fi
