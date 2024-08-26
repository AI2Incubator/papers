#!/bin/bash

# Check if Inkscape is installed
if ! command -v inkscape &> /dev/null
then
    echo "Inkscape is not installed. Please install it and try again."
    exit
fi

# Loop through all SVG files in the current directory
for svg_file in *.svg; do
    # Check if there are any SVG files in the directory
    if [ ! -f "$svg_file" ]; then
        echo "No SVG files found in the current directory."
        exit
    fi
    
    # Define the output PNG file name
    png_file="${svg_file%.svg}.png"
    
    # Convert the SVG file to PNG using Inkscape
    inkscape "$svg_file" --export-filename="$png_file"
    
    echo "Converted $svg_file to $png_file"
done

echo "All SVG files have been converted to PNG."

