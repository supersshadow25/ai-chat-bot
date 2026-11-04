eel.expose(DisplayMessage);
function DisplayMessage(message) {
    $(".siri-message .texts li").text(message);
    $('.siri-message').textillate('start');
}

eel.expose(ShowHood);
function ShowHood() {
    $("#Oval").attr("hidden", false);
    $("#SiriWave").attr("hidden", true);
}

eel.expose(senderText);
function senderText(message) {
    var chatBox = document.getElementById("chat-canvas-body");
    if (message.trim() !== "") {
        chatBox.innerHTML += `<div class="row justify-content-end mb-4">
            <div class = "width-size">
            <div class="sender_message">${message}</div>
        </div>`;
        chatBox.scrollTop = chatBox.scrollHeight;
    }
}

eel.expose(receiverText);
function receiverText(message) {
    var chatBox = document.getElementById("chat-canvas-body");
    if (message.trim() !== "") {
        chatBox.innerHTML += `<div class="row justify-content-start mb-4">
            <div class = "width-size">
            <div class="receiver_message">${message}</div>
            </div>
        </div>`;
        chatBox.scrollTop = chatBox.scrollHeight;
    }
}

eel.expose(hideLoader);
function hideLoader() {
    $("#Loader").attr("hidden", true);
    $("#FaceAuth").attr("hidden", false);
}

function showFaceAuthOptions() {
    $("#FaceAuth").attr("hidden", false);
    $("#faceAuthChoiceOverlay").css({ display: 'flex' });
}

function hideFaceAuthOptions() {
    $("#faceAuthChoiceOverlay").hide();
}

async function requestBrowserMicrophoneAccess() {
    const button = $("#allowMicrophoneBtn");
    button.prop("disabled", true).text("Requesting access...");

    try {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            throw new Error("Microphone access is not available in this browser context.");
        }

        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        stream.getTracks().forEach(track => track.stop());
        $("#microphoneAccessOverlay").hide();
        $("#microphoneAccessError").attr("hidden", true).text("");
        showFaceAuthOptions();
    } catch (error) {
        let message = error.message;
        if (error.name === "NotAllowedError" || error.name === "PermissionDeniedError") {
            let permissionState = "unknown";
            try {
                permissionState = (await navigator.permissions.query({ name: "microphone" })).state;
            } catch (permissionError) {
                // Some browser contexts do not expose microphone permission state.
            }

            if (permissionState === "granted") {
                message = "Edge allows this site, but Windows or a device policy blocked microphone access. In Windows Settings > Privacy & security > Microphone, enable Microphone access and Let desktop apps access your microphone.";
            } else if (permissionState === "denied") {
                message = "Edge still blocks microphone access for localhost. Open the site controls beside the address bar, set Microphone to Allow, then reload Jarvis.";
            } else {
                message = "Microphone access was denied by Edge or Windows. Allow Microphone for localhost in Edge site permissions and enable Let desktop apps access your microphone in Windows Settings > Privacy & security > Microphone.";
            }
        } else if (error.name === "NotFoundError" || error.name === "DevicesNotFoundError") {
            message = "No microphone was found. Connect or enable a microphone, then try again.";
        }
        $("#microphoneAccessError").text(message).removeAttr("hidden");
    } finally {
        button.prop("disabled", false).text("Allow microphone");
    }
}

eel.expose(hideFaceAuth);
function hideFaceAuth() {
    hideFaceAuthOptions();
    $("#FaceAuth").attr("hidden", true);
    $("#FaceAuthSuccess").attr("hidden", false);
}

eel.expose(hideFaceAuthSuccess);
function hideFaceAuthSuccess() {
    $("#FaceAuthSuccess").attr("hidden", true);
    $("#HelloGreet").attr("hidden", false);
}

eel.expose(hideStart);
function hideStart() {
    $("#Start").attr("hidden", true);
    setTimeout(function () {
        $("#Oval").addClass("animate__animated animate__zoomIn");
    }, 1000);
    setTimeout(function () {
        $("#Oval").attr("hidden", false);
    }, 1000);
}

$(document).ready(function () {
    $("#allowMicrophoneBtn").on("click", function () {
        requestBrowserMicrophoneAccess();
    });

    $("#skipMicrophoneBtn").on("click", function () {
        $("#microphoneAccessOverlay").hide();
        showFaceAuthOptions();
    });

    function submitFaceAuthChoice(choice) {
        const password = $("#adminPasswordInput").val();
        const name = $("#newUserNameInput").val();
        hideFaceAuthOptions();
        eel.handleFaceAuthChoice(choice, password, name);
    }

    $("#existingUserBtn").on("click", function () {
        submitFaceAuthChoice("existing");
    });

    $("#newUserBtn").on("click", function () {
        const password = $("#adminPasswordInput").val();
        const name = $("#newUserNameInput").val();
        if (!password || !name) {
            swal("Please enter the admin password and new user name.");
            return;
        }
        submitFaceAuthChoice("new");
    });
});