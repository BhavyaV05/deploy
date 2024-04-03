function openImageUploadForm() {
    document.getElementById('uploadForm').style.display = 'block';
    document.getElementById('img-up-button').style.display = 'none';
    document.getElementById('submit-button').style.display = 'block';
}

function allowDrop(event) {
    event.preventDefault();
    document.getElementById('uploadForm').classList.add('dragover');
}

function handleDrop(event) {
    event.preventDefault();
    document.getElementById('uploadForm').classList.remove('dragover');

    let files = event.dataTransfer.files;
    let fileInput = document.getElementById('fileInput');
    fileInput.files = files;
    handleFiles(files);
}

function handleFiles(files) {
    var previewFiles = document.getElementById('previewFiles');

    for (var i = 0; i < files.length; i++) {
        var file = files[i];

        if (file.type.startsWith('image/')) {
            // Use closure to capture the correct file
            (function (file) {
                var reader = new FileReader();

                reader.onload = function (e) {
                    var imageContainer = document.createElement('div');
                    imageContainer.classList.add('image-container');

                    var img = document.createElement('img');
                    img.src = e.target.result;
                    img.classList.add('scaled-image'); // Add this line to apply styling

                    imageContainer.appendChild(img);
                    previewFiles.appendChild(imageContainer);
                };

                reader.readAsDataURL(file);
            })(file);
        }
    }
}

// Open file input when clicking on the upload form
function uploadclick() {
    document.getElementById('fileInput').click();
}
document.getElementById('uploadForm').addEventListener('click', uploadclick);
