<?php
$style = $argv[1];
$target = $argv[2];
$base = $argv[3];

$sources = [];

function normalize_path($path)
{
    global $basedir;

    $realpath = realpath($path);
    $new_path = str_replace($basedir."/", "", $realpath);

    return $new_path ? $new_path : false;
}

$basedir = getcwd();

$deps = [];

$dom = new DOMDocument;
$dom->load($style);

foreach ( $dom->getElementsByTagName('FileSource') as $param) {
    $name = trim($param->getAttribute("name"));
    $path = trim($param->textContent);
    $sources[$name] = $path;
}


foreach ( $dom->getElementsByTagName('Parameter') as $param) {
    if ($param->getAttribute("name") == "file") {
        $path = normalize_path($base . "/" . trim($param->textContent));
        if ($path) $deps[] = $path;
    }
}

foreach ( $dom->getElementsByTagName('Map') as $param) {
    $file = $param->getAttribute("background-image");
    if ($file) {
        $path = normalize_path($base . "/" . $file);
        if ($path) $deps[] = $path;
    }
}

foreach ( ["Point", "Markers", "Shield", "LinePattern", "PolygonPattern"] as $type) {
    foreach ( $dom->getElementsByTagName($type.'Symbolizer') as $param) {
        $file = $param->getAttribute("file");
        if ($file) {
            $source = $param->getAttribute("base");
            if (isset($sources[$source])) {
                $file = $sources[$source]."/".$file;
            }
            $path = normalize_path($base . "/" . $file);
            if ($path) $deps[] = $path;
        }
    }    
}

echo "$target: $style " . implode(" ", $deps) . "\n";
?>
