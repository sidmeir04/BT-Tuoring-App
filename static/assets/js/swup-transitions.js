function uploads_init(){
    document.getElementById('imageUpload').addEventListener('change', function(event) {
        var reader = new FileReader();
        var imageElement = document.getElementById('image');
        var file = document.getElementById('imageUpload').files[0];
        
        if (file) {
            // Check if the uploaded file is a PDF
            if (file.type === "application/pdf") {
                console.log("s");  // Log "s" to the console for PDF files
                imageElement.src = "/static/assets2/img/pdfUploaded.jpg";  // Change image src if it's a PDF
            } else {
                // Read and display the image if the uploaded file is an image
                reader.onload = function(e) {
                    imageElement.src = e.target.result;
                };
                reader.readAsDataURL(file);
            }
        }
    });


    let currentPage = 1;
    const pages = document.querySelectorAll('.file-page');
    const itemsPerPage = 1;

    function updatePaginationControls() {
        const totalPages = pages.length;
        document.querySelector('.page-number').innerText = currentPage;
        document.querySelector('.prev-page').disabled = currentPage === 1;
        document.querySelector('.next-page').disabled = currentPage >= totalPages;
    }

    function showPage(page) {
        pages.forEach((pageElement, index) => {
            if (index + 1 === page) {
                pageElement.classList.remove('d-none');
                pageElement.classList.add('d-block');
            } else {
                pageElement.classList.remove('d-block');
                pageElement.classList.add('d-none');
            }
        });
        updatePaginationControls();
    }

    document.querySelector('.prev-page').addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            showPage(currentPage);
        }
    });

    document.querySelector('.next-page').addEventListener('click', () => {
        if (currentPage < pages.length) {
            currentPage++;
            showPage(currentPage);
        }
    });
    if (pages.length > 0) {
        showPage(1);  // Show the first page
    }
    updatePaginationControls()

    // Initialize with the first file being displayed, if files exist
    

    // Prevent the card click event when 'X' button is clicked
    function remove(event) {
        event.stopPropagation();  // Stop the click event from propagating to the parent card
        // Additional logic for removing or handling the file can be added here
        console.log('Remove button clicked');
    }
    function open_preview(num){
        // Open the modal and inject the file preview content
        var modal = document.getElementById('filePreviewModal');
        var filePreviewContent = document.getElementById('filePreviewContent');
        
        // Clear previous content
        filePreviewContent.innerHTML = '';
        isPDFs = [{%for file in session.files%}
        "{{ file.filename.endswith('.pdf') }}",
    {%endfor%}]
        urls = [{%for file in session.files%}
        "{{ url_for('display_file', file_id=file.id) }}",
    {%endfor%}]
        // Get file information (you might want to customize this based on file type)
        var isPDF = isPDFs[num] // Replace with dynamic check
        var fileUrl = urls[num]; // Dynamic file URL
        console.log(isPDF)
        if (isPDF) {
            // For PDF files, use an <embed> element
            filePreviewContent.innerHTML = `<embed src="${fileUrl}" type="application/pdf" width="100%" height="500px" />`;
        } else {
            // For image files, use an <img> element
            filePreviewContent.innerHTML = `<img src="${fileUrl}" alt="Preview" style="width: 100%; height: auto;" />`;
        }

        // Show the modal
        $(modal).modal('show');
    };
};
console.log('s')
uploads_init()