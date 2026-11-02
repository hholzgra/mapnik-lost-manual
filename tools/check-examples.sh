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

# check for specific Mapnik features being present
declare -A features
for feature in ArcSymbolizer
do
  if python3 -c 'import mapnik,sys; sys.exit(0 if hasattr(mapnik,"'"$feature"'") else 1)' 2>/dev/null
  then
	features["$feature"]=1
  else
	echo "  (skipping $feature examples, installed mapnik has no $feature)"
  fi
done

# check for shapefies needed by the example scripts
if [ ! -e examples/data/ne_110m_admin_0_countries_lakes.shp ] \
|| [ ! -e examples/data/ne_50m_graticules_30.shp ]
then
	echo "Natural Earth shapefiles missing, fetching them via 'make shapefiles'"
	make -s shapefiles || exit 1
fi

# when called with no speficif XML stylefiles to render -> render all
if [ $# -eq 0 ]
then
	set -- $(find examples -name '*.xml' -not -path '*/disabled/*' -and -not -path '*/tmp/*' | sort)
fi

failed=()

for xml in "$@"
do
	# skip over disabled or unavailable features
	case "$xml" in
		*/disabled/*) continue ;;
		*/tmp/*) continue ;;
		*/Arc/*) [ ! -v features["ArcSymbolizer"] ] && continue ;;
	esac

	# skip over already generated examples unless -f is in effect
	base=${xml%.xml}
	if [ $force -eq 0 ] && [ "$base.png" -nt "$xml" ] && [ "$base.svg" -nt "$xml" ]
	then
		continue
	fi

	# now actually render and track failures
	echo "  $xml"
	if ! examples/render.sh "$xml"
	then
		failed+=("$xml")
	fi
done

# print failure report
if [ ${#failed[@]} -gt 0 ]
then
	echo
	echo "Failed to render:"
	printf '  %s\n' "${failed[@]}"
	exit 1
fi
