function displayImages(images) {
    const imageGrid = document.getElementById('imageGrid');
    imageGrid.innerHTML = ''; // Clear previous content

    images.forEach((imageSrc) => {
        const img = document.createElement('img');
        img.src = imageSrc;
        img.classList.add('uploaded-image'); // Add a class for styling
        imageGrid.appendChild(img);
    });
}

function previewVideo() {
    // Get the image grid container
    var imageGrid = document.getElementById('imageGrid');

    // Check if there is an existing video
    var existingVideo = document.querySelector('video');
    if (existingVideo) {
        // Remove the existing video
        imageGrid.removeChild(existingVideo);
    }

    // Create a video element
    var video = document.createElement('video');
    video.controls = true; // Enable controls for the video
    video.style.maxWidth = '100%'; // Set maximum width to 100% of container

    // Create a source element and set its attributes
    var source = document.createElement('source');
    source.src = "{{ url_for('static', filename='icons/video_m1.mp4') }}"; // Set the correct path to your video file
    source.type = 'video/mp4'; // Set the type of the video

    // Append the source element to the video element
    video.appendChild(source);

    // Insert the video element above the "Preview Video" button
    var previewButton = document.querySelector('button:first-of-type'); // Get the first button (Preview Video)
    previewButton.parentNode.insertBefore(video, previewButton);

    // Play the video
    video.play();
}



function createVideo() {
    // Function for creating the video (if needed)
    // This can be implemented based on your requirements
}

// Fetch uploaded images from the server and display them on page load
window.addEventListener('load', function() {
    fetch('/uploaded_images')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayImages(data.images);
            } else {
                console.error('Failed to fetch uploaded images.');
            }
        })
        .catch(error => console.error('Error fetching uploaded images:', error));
});
