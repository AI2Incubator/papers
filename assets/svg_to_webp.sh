#!/bin/bash

# Check if ImageMagick (magick command) is installed
if ! command -v magick &> /dev/null
then
    echo "ImageMagick (magick command) could not be found. Please install it and try again."
    exit
fi

# Loop through all SVG files in the current directory
for svg_file in *.svg
do
    # Check if there are any SVG files in the directory
    if [ ! -f "$svg_file" ]; then
        echo "No SVG files found in the current directory."
        exit
    fi

    # Extract the filename without the extension
    base_name="${svg_file%.svg}"

    # Convert SVG to WebP using the magick command
    magick -background none "$svg_file" "$base_name.webp"

    # Confirm the conversion
    if [ $? -eq 0 ]; then
        echo "Converted: $svg_file -> $base_name.webp"
    else
        echo "Failed to convert: $svg_file"
    fi
done

echo "Conversion complete."

