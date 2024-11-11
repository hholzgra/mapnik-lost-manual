<?php

$file    = $argv[1];

$includes = parse_file($file);
sort($includes);

echo "$file: " . implode(" ", $includes) . "\n";

function parse_file($file, $dir = false) 
{
	$includes = [];

	$path = ($dir ? "$dir/" : "") . $file;

	foreach (file($path) as $line) {
		$line = trim($line);
	
		if (empty($line)) continue;
		if (preg_match('|^\s*//|', $line)) continue;
		if (preg_match('/include::([^\[]+)/', $line, $m)) {
			$new_file = normalize($m[1], $dir);
			$includes[$new_file] = $new_file;
			if (preg_match('|\.adoc$|', $new_file)) {
			  $new_dir = dirname($new_file);
			  $new_base = basename($new_file);
			  $new_includes = parse_file($new_base, $new_dir);
			  $includes = array_merge($includes, $new_includes);
			}
		}
		if (preg_match('/image::([^\[]+)/', $line, $m)) {
			$arg = normalize($m[1]);
			$includes[$arg] = $arg;
		}	
	}
	return $includes;
}

function normalize($arg, $dir = false) 
{
	if (preg_match('|\{sourcedir\}/(.*)|', $arg, $m)) {
		return $m[1];
	}
	if ($dir) return "$dir/$arg";
	return $arg;
}
?>
