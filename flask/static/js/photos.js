// Declare used variables
const formElement = document.getElementById('dropzoneForm');
let formSubmitted = false;
const dropArea = document.getElementById('drop-area');
const fileElem = document.getElementById('drop-file-elem');
const collection = document.getElementById('collection').value;
const docId = document.getElementById('doc-id') ? document.getElementById('doc-id').value : 0;
const maxFileSize = 1024 * 1024;
const allowedFileExtensions = ['jpg', 'jpeg', 'png', 'gif'];

/** 
* Converts bytes to readable format.
* @credit https://stackoverflow.com/questions/15900485/correct-way-to-convert-size-in-bytes-to-kb-mb-gb-in-javascript
* @param {number} bytes - Number of bytes.
* @param {int} decimals - Number of decimals.
* @return {string} Formated size.
*/
const formatBytes = (bytes, decimals = 2) => {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];

    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

/** 
* API GET function. Gets the data from the url and sends it as a parameter to the callback function.
* @param {string} method - Request method
* @param {string} url - Api url to be called
* @param {function} cb - Callback function
*/
const apiRequest = (method, url, cb, data = undefined) => {
    const xhr = new XMLHttpRequest();

    xhr.onreadystatechange = function () {
        if (this.readyState == 4) {
            if (this.status == 200) {
                cb(JSON.parse(this.responseText), this.status);
            } else {
                cb({}, this.status);
            }
        }
    };

    xhr.onerror = function () {
        cb({}, this.status);
    };

    xhr.open(method, url);
    xhr.send(data);
}

/**
* Adds .highlight class to the drop area element.
*/
const highlight = () => {
    dropArea.classList.add('highlight');
}

/**
* Removes .highlight class from the drop area element.
*/
const unhighlight = () => {
    dropArea.classList.remove('highlight');
}

/**
* Updates the hidden input with uploaded filenames list.
*/
const fileListUpdate = () => {
    const fileListInput = document.getElementById('photo_list');
    const fileList = [];
    document.querySelectorAll('.photo-container').forEach(el => {
        fileList.push(el.dataset.cloudinary);
    });
    if (fileListInput) fileListInput.value = fileList.join(',');
    if (lightbox) {
        lightbox.reload();
    }
}

/**
* Function called when drop area is clicked and it triggers click on the file input.
*/
const handleClick = () => {
    fileElem.click();
}

/**
 * Handles the dropped files.
* @credit https://www.smashingmagazine.com/2018/01/drag-drop-file-uploader-vanilla-js/
* @param {obj} e - event object.
*/
const handleDrop = (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;

    handleFiles(files);
}

/**
* Handles a set of files by calling Upload function for each.
* If the drag&drop area is not set to multiple, then an ajax DELETE request is sent to delete the current file.
* @param {obj} files - files object.
*/
const handleFiles = (files) => {
    if (dropArea.dataset.multiple == "true") {
        ([...files]).forEach((file) => {
            const fileExtension = file.name.split(".").pop().toLowerCase();
            if (file.size > maxFileSize) {
                alertToast("File <strong>" + file.name + "</strong> is too large. Maximum allowed is <strong> " + formatBytes(maxFileSize) + " </strong>");
            } else if ((!allowedFileExtensions.includes(fileExtension)) || (file.type.split("/")[0] != "image")) {
                alertToast("File <strong>" + file.name + "</strong> type (" + fileExtension + ") is not allowed!");
            } else {
                // getSignedRequest(file);
                uploadFile(file);
            }
        });
    } else {
        const fileExtension = files[0].name.split(".").pop().toLowerCase();
        if (files[0].size > maxFileSize) {
            alertToast("File <strong>" + files[0].name + "</strong> is too large. Maximum allowed is <strong> " + formatBytes(maxFileSize) + " </strong>");
        } else if ((!allowedFileExtensions.includes(fileExtension)) || (files[0].type.split("/")[0] != "image")) {
            alertToast("File <strong>" + files[0].name + "</strong> type (" + fileExtension + ") is not allowed!");
        } else {
            // check if there is a current file
            if (document.querySelectorAll('.photo-container')[0]) {
                if (confirm('Are you sure?\r\n This will replace the current file!')) {
                    const el = document.querySelectorAll('.photo-container')[0];
                    deleteFile(el);
                } else {
                    return;
                }
            }
            // getSignedRequest(files[0]);
            uploadFile(files[0]);
        }
    }
}

/** 
* Sends request to AWS S3 server delete url to delete file from cloud
* and calls function to delete file metadata from database deleteFileFromDb
* and removes the image element from DOM
* @param {obj} el - DOM el that contains file metadata and that has to be removed.
*/
const deleteFile = (el) => {
    const file_id = el.dataset.fileid;
    // const fileName = el.dataset.src.split('/').pop();
    const url = urlForDeleteCloud + "?file_id=" + file_id;

    apiRequest("GET", url, (response, status) => {
        if (status === 200) {
            if (docId) {
                deleteFileFromDb(file_id);
            }
            el.remove();
            fileListUpdate();
            alertToast("Image '" + file_id + "' was successfully deleted!");
        }
        else {
            alertToast("Could not delete.");
        }
    });
}

// /** 
// * Sends request to python route to get signed request that is then passed through upladFile function
// * @param {obj} file - file to be uploaded
// */
// const getSignedRequest = (file) => {
//     const fileExt = file.name.split('.').pop().toLowerCase();
//     const date = new Date();
//     const newFileName = collection + String(date.getDate()) + String(date.getMonth() + 1) + Math.floor(Math.random() * 999) + '.' + fileExt;
//     const renamedFile = new File([file], newFileName, { type: file.type });
//     const url = urlForSignS3 + "?file_name=" + renamedFile.name + "&file_type=" + renamedFile.type;

//     apiRequest("GET", url, (response, status) => {
//         if (status === 200) {
//             uploadFile(renamedFile, response.data, response.url);
//         }
//         else {
//             alertToast("Could not get signed URL.");
//         }
//     });
// }

/** 
* Send request to AWS S3 server to upload file
* Calls function to add file to database addFileToDb(url)
* Adds new image element to DOM
* @param {obj} file - File to be uploaded
* @param {array} s3Data - Data from signed request
* @param {string} url - File url from signed request
* @return {ReturnValueDataTypeHere} Brief description of the returning value here.
*/
// const uploadFile = (file, s3Data, url) => {
const uploadFile = (file) => {
    const fileExt = file.name.split('.').pop().toLowerCase();
    const date = new Date();
    const newFileName = collection + String(date.getDate()) + String(date.getMonth() + 1) + Math.floor(Math.random() * 999) + '.' + fileExt;
    const renamedFile = new File([file], newFileName, { type: file.type });
    const postData = new FormData();

    // for (key in s3Data.fields) {
    //     postData.append(key, s3Data.fields[key]);
    // }
    postData.append('file', renamedFile);

    apiRequest("POST", urlForUploadPhoto, (response, status) => {
        if (status === 200 || status === 204) {
            let photo_data = response.data
            let url = photo_data.url
            let fileid = photo_data.public_id

            if (docId) {
                addFileToDb(JSON.stringify(photo_data));
            }
            if (document.getElementById('gallery')) {
                const containerEl = document.getElementById('gallery');
                const existingElCount = document.querySelectorAll(".photo-container").length;
                const imgTag = `<a href="${url}" class="${collection}-gallery">
                                        <img class="img-thumbnail gallery-item" src="${url}" alt="photo">
                                    </a>`;
                const newEl = Object.assign(document.createElement('div'), {
                    className: 'photo-container col-sm-4 col-md-6 col-lg-4',
                    innerHTML: `${imgTag}
                                    <a class="delete-photo btn btn-danger" data-photo-key="${existingElCount}">
                                        <i class="bi bi-trash-fill"></i>
                                    </a>`
                });
                newEl.dataset.src = url;
                newEl.dataset.fileid = fileid;
                newEl.dataset.cloudinary = JSON.stringify(photo_data);
                containerEl.appendChild(newEl);
                alertToast("Image '" + file.name + "' was successfully uploaded!");
            }
            fileListUpdate();
        }
        else {
            alertToast("Could not upload file.");
        }
    }, postData);
}

/** 
* Sends request to python route to add file to db into specified collection and document
* @param {string} photo - Full url of the photo
*/
const addFileToDb = (photo_data) => {
    // const url = urlForSavePhoto + "?coll=" + collection + "&docid=" + docId + "&photo=" + photo;

    const postData = new FormData();
    postData.append('coll', collection);
    postData.append('docid', docId);
    postData.append('photo_data', photo_data);

    apiRequest("PUT", urlForSavePhoto, (response, status) => {
        alertToast(response.message)
    }, postData);
}

/**
* Sends request to python route to delete file from database
* @param {string} photo - Full url of the photo
*/
const deleteFileFromDb = (file_id) => {
    const url = urlForDeletePhoto + "?coll=" + collection + "&docid=" + docId + "&file_id=" + file_id;

    apiRequest("GET", url, (response, status) => {
        if (status === 500) {
            alertToast("Error updating database");
        } else {
            alertToast(response.message)
        }
    });
}

/** 
* Generates an array out of dom photos src of a particular class
* for use of image insertion in TinyMCE rich text editor
* @return {array} generated array of photo sources
*/
const getPhotoList = () => {
    if (document.querySelectorAll('.photo-container').length) {
        const photoList = [];
        document.querySelectorAll('.photo-container').forEach((el, i) => {
            photoList.push({ title: 'Photo' + (i + 1), value: el.getElementsByTagName('img')[0].src });
        });

        return photoList;
    } else {
        return [];
    }
}

/**
* Delay function
* @credit https://www.perimeterx.com/tech-blog/2019/beforeunload-and-unload-events/
* @param {number} delay - miliseconds.
*/
const sleep = (delay) => {
    const start = new Date().getTime();
    while (new Date().getTime() < start + delay);
}

// Event Delegation for dynamic created elements
// Click event listener for file delete button
document.getElementById('gallery').addEventListener('click', (e) => {
    if (e.target.classList.contains('delete-photo') || e.target.classList.contains('bi-trash-fill')) {
        preventDefaults(e);
        if (confirm('Are you sure?\r\n This will delete file and remove it from the database!')) {
            let delete_target;
            if (e.target.classList.contains('delete-photo')) {
                delete_target = e.target.parentElement;
            } else {
                delete_target = e.target.parentElement.parentElement;
            }
            deleteFile(delete_target);
        }
    }
});

// Event listener for form submission
if (formElement) {
    formElement.addEventListener('submit', () => {
        formSubmitted = true;
    });
}

// Check if db doc id is set (if is set then page is on an edit form)
if (!docId) {
    // Prevent leaving page if any existing uploads (except for submit)
    window.onbeforeunload = () => {
        showSpinner();
        setTimeout(() => { hideSpinner() }, 2000); // Only hides the spinner if user cancels unload
        if (document.querySelectorAll('.photo-container').length && !formSubmitted) {
            return "Are you sure you want to leave?";
        } else {
            return;
        }
    };
    // Delete uploaded files on page unload
    window.onunload = () => {
        if (document.querySelectorAll('.photo-container').length && !formSubmitted) {
            document.querySelectorAll('.photo-container').forEach(el => {
                deleteFile(el);
            });
            sleep(2000);
        }
    };
}

// Drag&Drop event listeners
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, preventDefaults, false);
});
['dragenter', 'dragover'].forEach(eventName => {
    dropArea.addEventListener(eventName, highlight, false);
});
['dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, unhighlight, false);
});
dropArea.addEventListener('drop', handleDrop, false);

// Click on the drag&drop area event listener
dropArea.addEventListener('click', handleClick, false);

// File input change event listener
fileElem.onchange = () => {
    handleFiles(fileElem.files);
    fileElem.value = "";
};