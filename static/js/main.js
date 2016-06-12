var ws = new WebSocket('ws://' + location.host + '/ws');
var onaddstreamcalled = 0;
var ICE_config = {
    'iceServers': [{
        url: 'stun:stun01.sipphone.com'
    }, {
        url: 'stun:stun.ekiga.net'
    }, {
        url: 'stun:stun.fwdnet.net'
    }, {
        url: 'stun:stun.ideasip.com'
    }, {
        url: 'stun:stun.iptel.org'
    }, {
        url: 'stun:stun.rixtelecom.se'
    }, {
        url: 'stun:stun.schlund.de'
    }, {
        url: 'stun:stun.l.google.com:19302'
    }, {
        url: 'stun:stun1.l.google.com:19302'
    }, {
        url: 'stun:stun2.l.google.com:19302'
    }, {
        url: 'stun:stun3.l.google.com:19302'
    }, {
        url: 'stun:stun4.l.google.com:19302'
    }, {
        url: 'stun:stunserver.org'
    }, {
        url: 'stun:stun.softjoys.com'
    }, {
        url: 'stun:stun.voiparound.com'
    }, {
        url: 'stun:stun.voipbuster.com'
    }, {
        url: 'stun:stun.voipstunt.com'
    }, {
        url: 'stun:stun.voxgratia.org'
    }, {
        url: 'stun:stun.xten.com'
    }, {
        url: 'turn:numb.viagenie.ca',
        credential: 'muazkh',
        username: 'webrtc@live.com'
    }, {
        url: 'turn:numb.viagenie.ca:3478',
        username: 'sanchit.goel1123@gmail.com',
        credential: 'qwerty'
    }, {
        url: 'turn:192.158.29.39:3478?transport=udp',
        credential: 'JZEOEt2V3Qb0y27GRntt2u2PAYA=',
        username: '28224511:1379330808'
    }, {
        url: 'turn:192.158.29.39:3478?transport=tcp',
        credential: 'JZEOEt2V3Qb0y27GRntt2u2PAYA=',
        username: '28224511:1379330808'
    }]
}
var $toastcontent=$('<div id="dialog-message" >'+
                    '<button id="btn-reject" class="btn left red waves-effect waves-light" onclick="reject()">Reject</button>'+
                    '<button id="btn-accept" class="btn right green waves-light waves-effect" onclick="accept()" >Receve</button>'+
                  '</div>');
var initiator;
var acceptoffer;
var pc = new RTCPeerConnection(ICE_config);
var globalsignal;

notifyoffer();

function call() {
    $('#btn-call').addClass('btn-active');
    initiator = true;
    init();
    //setTimeout(call, 10000)
}

function receive() {
    $('#btn-receive').addClass('btn-active');
    initiator = false;
    init();
}

function accept() {
    $('#btn-accept').addClass('btn-active');
    $('.toast').remove();
    acceptoffer=1;
    notifyoffer();
}

function reject() {
    $('#btn-accept').addClass('btn-active');
    $('.toast').remove()
    ws.send(JSON.stringify({
        "accept": 0
    }));
}


function init() {
    var constraints = {
        audio: $('#audio').prop('checked'),
        video: $('#video').prop('checked')
    };

    if (constraints.audio || constraints.video) {
        getUserMedia(constraints, connect, fail);
    } else {
        connect();
    }
}

function notifyoffer(stream) {
    pc.onicecandidate = function(event) {
        console.log(event.candidate)
        if (event.candidate) {
            ws.send(JSON.stringify(event.candidate));
        }
    };
    pc.onaddstream = function(event) {
        console.log(event)
        $('#remote').attachStream(event.stream);
        logStreaming(true);
    };
    if (stream) {
        pc.addStream(stream);
        $('#local').attachStream(stream);
    }

    ws.onmessage = function(event) {
        var signal = JSON.parse(event.data)
        if (signal.type == "offer" || signal.sdp) {
            globalsignal = signal;
            Materialize.toast($toastcontent,10000)      
        }
        else if (signal.candidate) {
            pc.addIceCandidate(new RTCIceCandidate(signal));
        }
    }
    if (acceptoffer==1){
        $('#btn-accept').addClass('btn-active');
        $('.toast').remove();
        var constraints = {
            audio: $('#audio').prop('checked'),
            video: $('#video').prop('checked')
        };

        if (constraints.audio || constraints.video) {
            getUserMedia(constraints, (function(stream){if (stream) {
                                                console.log(stream)
                                                pc.addStream(stream);
                                                $('#local').attachStream(stream);
                                                }}), fail);
        } else {
            (function(){});
        }
        initiator = false;
        receiveOffer(globalsignal);
        ws.send(JSON.stringify({
            "accept": 1
        }))
    }
}



function connect(stream) {
    if (stream) {
        pc.addStream(stream);
        $('#local').attachStream(stream);
    }

    pc.onaddstream = function(event) {
        $('#remote').attachStream(event.stream);
        logStreaming(true);
    };
    pc.onicecandidate = function(event) {
        console.log(event.candidate)
        if (event.candidate) {
            ws.send(JSON.stringify(event.candidate));
        }
    };
    ws.onmessage = function(event) {
        console.log(event)
        var signal = JSON.parse(event.data);
        if (signal.sdp) {
            receiveAnswer(signal);
        } else if (signal.candidate) {
            pc.addIceCandidate(new RTCIceCandidate(signal));
        }
    };

    if (initiator) {
        createOffer();
    } else {
        log('waiting for offer...');
    }
    logStreaming(false);
}


function createOffer() {
    log('creating offer...');
    pc.createOffer(function(offer) {
        log('created offer...');
        pc.setLocalDescription(offer, function() {
            log('sending to remote...');
            ws.send(JSON.stringify(offer));
        }, fail);
    }, fail);
}


function receiveOffer(offer) {
    log('received offer...');
    pc.setRemoteDescription(new RTCSessionDescription(offer), function() {
        log('creating answer...');
        pc.createAnswer(function(answer) {
            log('created answer...');
            pc.setLocalDescription(answer, function() {
                log('sent answer');
                ws.send(JSON.stringify(answer));
            }, fail);
        }, fail);
    }, fail);
}


function receiveAnswer(answer) {
    log('received answer');
    pc.setRemoteDescription(new RTCSessionDescription(answer));
}


function log() {
    $('#status').text(Array.prototype.join.call(arguments, ' '));
    console.log.apply(console, arguments);
}


function logStreaming(streaming) {
    $('#streaming').text(streaming ? '[streaming]' : '[..]');
}


function fail() {
    $('#status').text(Array.prototype.join.call(arguments, ' '));
    $('#status').addClass('error');
    console.error.apply(console, arguments);
}


jQuery.fn.attachStream = function(stream) {
    this.each(function() {
        this.src = URL.createObjectURL(stream);
        this.play();
    });
};