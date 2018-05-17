var SERVER = "";
var dialog = document.getElementById('dialog');
var dialogText = document.getElementById('dialogText');
var dialogOkCancel = document.getElementById('dialogOkCancel');
var dialogOk = document.getElementById('dialogOk');
var irEmitter = document.getElementById('irEmitter');
var codeName = document.getElementById('codeName');
var currentAction;

function sendCode(code) {
    sendRequest(SERVER + "send/" + irEmitter.selectedIndex + "/" + code,
        processResponse);
}

function learnCode() {
    sendRequest(SERVER + "learn/" + codeName.value, processResponse);
}

function processResponse(response) {
    if (response.result === 'failure') {
        showMessage("Error learning code: " + response.error);
    } else if (typeof response.message !== 'undefined') {
        showMessage(response.message);
    }
}

function sendRequest(uri, callback) {
    var request = new XMLHttpRequest();
    request.open("POST", uri, true);
    request.setRequestHeader("Content-type", "application/json");
    request.onloadend = function() {
            if (request.status == 0) {
                callback({ result: 'failure', error: 'Network error'});
            } else {
                callback(JSON.parse(request.responseText));
            }
    };
    request.send();
}

function confirmDeleteCode(code) {
    currentAction = deleteCode(code);
    showDialog("Are you sure you want to delete code " + code + "?");
}

function confirmClearCodes() {
    currentAction = clearCodes;
    showDialog("Are you sure you want to delete all codes?");
}

function deleteCode(code) {
    return function() {
        sendRequest(SERVER + "remove/" + code, processResponse);
    }
}

function clearCodes() {
    sendRequest(SERVER + "clear", processResponse);
}

function showDialog(text) {
    dialogText.innerHTML = text;
    dialogOkCancel.style.display = "block";
    dialogOk.style.display = "none";
    dialog.style.display = "block";
}

function showMessage(text) {
    dialogText.innerHTML = text;
    dialogOkCancel.style.display = "none";
    dialogOk.style.display = "block";
    dialog.style.display = "block";
}

function confirmAction() {
    hideDialog();
    if (typeof currentAction !== "undefined") {
        currentAction();
        currentAction = null;
    }
}

function cancelAction() {
    hideDialog();
    currentAction = null;
}

function hideDialog() {
    dialog.style.display = "none";
}
