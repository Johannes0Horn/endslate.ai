/* eslint-disable no-undef */
/* eslint-disable no-unused-vars */
var csInterface;
var appName;
var appVersion;
var APIVersion;
var caps;
var ws;

var paths;
var port;
// child process itself also imports process
var childProcess = require('child_process');
const fs = require('fs');


var settingspath
//win 64 also return win 32
if (process.platform === "win32") {
    settingspath = process.env.LOCALAPPDATA;
} else if (process.platform === "darwin") {
    settingspath = '/Library/Application Support/';
} else {
    console.log("error unsuported OS");
}

async function checkIfBackendAlive(_port) {
    //check if backend is alive on this port, stopping after timeout
    var checkedIfBackendAlive_result;
    var checkedIfBackendAlive = false
    var test_ws = new WebSocket("ws://127.0.0.1:" + _port + "/");

    test_ws.onerror = function () {
        console.log("Cannot connect to server- Backend not alive on Port " + _port);
        checkedIfBackendAlive_result = false;
    };

    test_ws.onopen = function (event) {
        console.log("Connected on Port" + _port);
        console.log("Checking if its slateAI Backend");
        test_ws.send("ping");
    };

    test_ws.onmessage = function (event) {
        console.log(event.data);
        if (event.data = "slateai alive on Port " + _port) {
            console.log("slateAI connection confirmed")
            checkedIfBackendAlive_result = true;
        }
        //test_ws can be closed now, not needed anymore
        test_ws.close();

    };
    //test_ws gets closed no matter what
    test_ws.onclose = function (event) {
        console.log("closing Test websocket.");
        //remove test Websocket
        test_ws = undefined;
        checkedIfBackendAlive = true
    }

    //wait for result
    console.log("wait for checkIfBackendAlive Result.");
    var seconds = 0
    while (true) {
        console.log("checkIfBackendAlive for ", seconds, " seconds.")
        //poll every 1000 milliseconds
        await new Promise(r => setTimeout(r, 1000));
        if (checkedIfBackendAlive == true) {
            return checkedIfBackendAlive_result;
        }
        seconds++;
    }

}


function showVersionInfo(data) {
    document.getElementById("outputtest").innerHTML = data;
}

function showAPIVersionInfo(data) {
    document.getElementById("outputtest").innerHTML = data;
}


//get path from premiere and send them with "fetchProjectItemPaths()" to the backend
function orderProjectItemPaths() {
    console.log("order Paths from Premiere")
    csInterface.evalScript('$._PPP_.getSelectedItemPaths()', fetchProjectItemPaths);
}

function fetchProjectItemPaths(pathdata) {
    console.log("received Paths from Premiere: ", pathdata)
    paths = pathdata.split(",");
    console.log("paths: ", paths);
    if (!paths.includes("undefined")) {
        console.log("sending paths to Backend: ", paths);
        ws.send(paths);
    } else {
        csInterface.evalScript('$._PPP_.updateEventPanel("No items Selected.")');
    }

}


function calculatePercentageProgressbar(remaining, total) {
    if (total > 0) {
        var steps = total / 100;
        var result = (total - remaining + 1) / steps;
        return result;
    } else return 0;
}

function updateProgressbar(remaining, total) {
    if (total == 0) {
        $("#allprogressbar").css('width', calculatePercentageProgressbar(remaining, total) + '%');
        $("#progressbarTextinfo").html("no Clips to analyse");
    } else {
        $("#allprogressbar").css('width', calculatePercentageProgressbar(remaining, total) + '%');
        updateTextProgressbar(remaining, total);
    }
}

function promptMessageDone(show) {
    if (show == true) {
        $("#promtDone").show();
    } else {
        $("#promtDone").hide();
    }
}

function updateTextProgressbar(remaining, total) {
    var calculate_remaining_clips = total - remaining + 1;
    if (calculate_remaining_clips > total) {
        calculate_remaining_clips = total;
    }

    var text_to_display = "Analysing Clip " + calculate_remaining_clips + "/" + total
    $("#progressbarTextinfo").html(text_to_display);
}

function activatePauseButton() {
    var button = $("#pauseButton");
    $("#pauseButton").show();
}

function deactivatePauseButton() {
    var button = $("#pauseButton");
    $("#pauseButton").hide();
    $("#pauseButton").html("Pause");
    $("#pauseButton").css('background-color', 'red');
}

function togglePauseButton() {
    var button = $("#pauseButton");
    if (button.html() == "Resume") {
        //is in Pause modus, chainging to Resume
        button.html("Pause");
        button.css('background-color', 'red');
        //todo deactivate button until send
        ws.send("RESUME");

    } else {
        //is in Resume modus, chainging to Pause
        button.html("Resume");
        button.css('background-color', 'green');
        //todo deactivate button until send
        ws.send("PAUSE");
    }

}

function showProjectItemPaths(data) {
    paths = data;
    data = data.split(",");
    document.getElementById("outputtest").innerHTML = "";
    pathCounter = 0;
    while (pathCounter < data.length) {
        document.getElementById("outputtest").innerHTML += data[pathCounter] + "<br>";
        pathCounter++;
    }
}

function receiveMessage(message) {
    //check if message is empty
    if (message != undefined && message != "") {
        console.log(message);
        //check if message is a ping
        if (message.includes("Server alive on Port")) {
            //still connected to server
            console.log("still connected to server");
        }
        //check if message is statusinfo of Backend
        else if (message.includes("Statusinfo")) {
            updateStatus(JSON.parse(message));
        } else if (message.toString() == "Done") {
            console.log("Queue completeley processed!");
            promptMessageDone(true);

        }
        //check if message is a device info update
        else if (message.includes("possibleDevices")) {
            var possibleDevices = JSON.parse(message)['possibleDevices'];
            var devices = possibleDevices['devices'];
            var expirimental_devices = possibleDevices['experimentalDevices'];
            document.getElementById("myDropdown").innerHTML = "";
            for (i = 0; i < devices.length; i++) {
                document.getElementById("myDropdown").innerHTML += "<a>" + devices[i] + "</a>";
            }
            for (i = 0; i < expirimental_devices.length; i++) {
                document.getElementById("myDropdown").innerHTML += "<a>" + expirimental_devices[i] + " (experimental)" + "</a>";
            }
            deviceitems = document.getElementById("myDropdown").getElementsByTagName("a");
            for (i = 0; i < deviceitems.length; i++) {
                console.log("onclick = deviceChosen");
                deviceitems[i].onclick =

                    function (e) {
                        console.log("deviceChosen: " + e.target.innerHTML)
                        dropdown = document.getElementById("plaidmldropdownbutton");
                        //send device change to backend only if it is changed
                        if (e.target.innerHTML != dropdown.innerHTML) {
                            dropdown.innerHTML = "changing device...";
                            ws.send("SETDEVICE:" + e.target.innerHTML);
                        }

                    }
            }
        }
        //check if message is a device picking update
        else if (message.includes("chosenDevice")) {
            var chosenDevice = JSON.parse(message)['chosenDevice'];
            document.getElementById("plaidmldropdownbutton").innerHTML = chosenDevice;

        }
        else {
            //message is an analyzed result
            //convert String to dict
            var currentPathClapTimesDict = JSON.parse(message);
            //get Path and Time
            var currentPath = Object.keys(currentPathClapTimesDict)[0];
            var currentTimes = currentPathClapTimesDict[currentPath];
            console.log("currentTimes:", currentTimes);
            //add marker(s)
            var csInterface = new CSInterface();
            // replace "\" with "/" so they dont get deleted when used as parameter
            currentPath = currentPath.split("\\").join("/");
            for (var i = 0; i < currentTimes.length; i++) {
                var addClipcommand = '$._PPP_.addClipMarker("' + currentPath + '",' + currentTimes[i] + ', app.project.rootItem, "' + process.platform + '")';
                console.log(addClipcommand);
                csInterface.evalScript(addClipcommand);
            }
        }
    } else {
        console.log("WARNING: received empty message");
    }
}

function updateStatus(statusinfo) {
    var itemsRemaining = statusinfo['Statusinfo']['itemsRemaining'];
    var currentItem = statusinfo['Statusinfo']['current'];
    var totalItems = statusinfo['Statusinfo']['totalItems'];
    var activeDevice = statusinfo['Statusinfo']['activeDevice'];
    var experimental = statusinfo['Statusinfo']['experimental'];
    updateProgressbar(itemsRemaining, totalItems);
    $("#itemsRemaining").html("Items remaining:" + itemsRemaining);
    if (itemsRemaining == 0) {
        //idle
        deactivatePauseButton();
        $("#FindClapsText").html("Find Claps");
        $("#currentItem").html("");
    } else {
        activatePauseButton();
        promptMessageDone(false);
        $("#FindClapsText").html("Add Files to Queue");
        $("#currentItem").html("Current Item:" + currentItem);
    }
    //update chosen Device
    if (experimental == true) {
        activeDevice += " (experimental)"
    }
    document.getElementById("plaidmldropdownbutton").innerHTML = activeDevice;
}



async function portInUse(_port) {
    var net = require('net');
    const client = new net.Socket();
    var inUse = null;
    client.on('end', function () {
        //Port in Use, ended
        console.log("port " + _port + "is in use");
        inUse = true;
    });

    client.on('error', function (err) {
        console.log("Error: " + err.message);
        //Port not in Use, nothing to connect to
        console.log("port " + _port + "is not in use");
        inUse = false;
    })

    //try to connect to localhost via _port
    client.connect({ port: _port, host: 'localhost' });

    //wait for response
    while (true) {
        await new Promise(r => setTimeout(r, 100));
        if (inUse != null) {
            return inUse;
        }
    }

}


async function findOpenPort() {
    for (var i = 0; i < 100; i++) {
        var currentPort = 3333 + i;
        var in_use = await portInUse(currentPort)
        console.log("in_use", in_use)
        if (!in_use) {
            return currentPort;
        }
    }
    console.log("unable to find open port. Using Port 3333 as default.")
    return 3333;
}

async function startBackend(_port) {
    _port = _port.toString();
    console.log("port as string: ", _port);
    var backendDir = getBackendDir();
    if (!backendDir) {
        console.log("didnt start backend, because no BackendDir Found!");
        return;
    }
    var executableName
    if (process.platform === "win32") {
        executableName = "slateAI.exe";
    } else if (process.platform === "darwin") {
        executableName = "./slateAI";

    }
    console.log("Starting backend from" + backendDir)
    childProcess.exec(executableName + ' ' + _port, { cwd: backendDir },
        (error, stdout, stderr) => {
            if (error) {
                throw error;
            }
            console.log(stdout);
        });
    console.log("backend invoked");
}

function saveUsedPort(_port) {
    //get destination folder
    //if settings folder doesnt exist, create it
    if (!fs.existsSync(settingspath + "/slateAI")) {
        fs.mkdirSync(settingspath + "/slateAI");
    }

    //read config.json if it exists, otherwise create it
    if (fs.existsSync(settingspath + "/slateAI/config.json")) {
        var conf_json_data = JSON.parse(fs.readFileSync(settingspath + "/slateAI/config.json", 'utf8'));
    }
    else{
        var conf_json_data = {};
    }
    //add port to conf_data
    conf_json_data['port'] = _port;
    //save config.json
    fs.writeFileSync(settingspath + "/slateAI/config.json", JSON.stringify(conf_json_data));
    console.log("Port " + _port + " written to " + settingspath + "/slateAI/config.json");
}

function getBackendDir() {
    //WINDOWS
    if (process.platform === "win32") {
        //get batchFilePath
        var loc = window.location.pathname;
        var dir = decodeURI(loc.substring(1, loc.lastIndexOf('/')));
        var batchpath = dir + "/lib/getBackenDirs.bat";
        //execute Batchfile
        var child_process = require('child_process');
        var child = child_process.spawnSync(batchpath, {
            encoding: 'utf8'
        });
        if (child.error) {
            console.log("ERROR: ", child.error);
        }
        //retrieve Paths from batchFile
        BackendDirs = child.stdout.split(";");
        //Filter empty Paths
        BackendDirsFiltered = [];
        for (var i = 0; i < BackendDirs.length; i++) {
            currentPath = BackendDirs[i].replace(/(\r\n|\n|\r)/gm, "");
            if (currentPath.length > 1) {
                BackendDirsFiltered.push(currentPath);
            }
        }
        //get unique paths
        BackendDirs = Array.from(new Set(BackendDirsFiltered))
        console.log(BackendDirs);
        if (BackendDirs.length == 0) {
            console.log("Warning: No Backend Found.");
            return false;
        }
        if (BackendDirs.length > 1) {
            console.log("Warning: more than one Location for Backend Found. Using ", BackendDirs[0])
        }
        return BackendDirs[0];
    } else if (process.platform === "darwin") {
        //MAC standard installation path
        return "/Applications/EndSlateai.app/Contents/MacOS/"
        //MAC assume app is on desktop	
        //const homeDir = require('os').homedir();
        //const desktopDir = `${homeDir}/Desktop`;
        //return desktopDir + "/slateAI.app/Contents/MacOS/";
    }
}

function endBackend() {
    //todo, do we need this function?
}


function connectToBackend(_port) {
    if (_port == undefined) {
        console.log("Missing port, looking for new one")
        _port = findOpenPort();
        console.log("Found open port", _port)
    }
    console.log("start websocket with Port " + _port);
    ws = new WebSocket("ws://127.0.0.1:" + _port + "/");

    ws.onerror = function () {
        console.log("Cannot connect to server");
    };
    //it takes some time until websocket is connected
    ws.onopen = function (event) {
        console.log("WebSocket is open now.");
        ws.onmessage = function (event) {
            receiveMessage(event.data);
        };
        console.log("connected to backend on port ", _port);
        ws.send("GETDEVICES");
        activateButton();
    };
    //get rid of websocket if it disconnects -> means if backend terminates
    ws.onclose = function (event) {

        console.log("closing websocket. Trying to reconnect");
        document.getElementById("buttonOverlayText").innerHTML = "Trying to reconnect to Backend...";
        //remove Websocket
        ws = undefined;
        deactivateButton();
        // waiting for backend to restart
        connectToBackend(_port);

    }
}

function activateButton() {
    $("#buttonOverlay").hide();
}

function deactivateButton() {
    $("#buttonOverlay").show();
}

function refreshPanel() {
    history.go(0);
}

async function initSlateAIExtension() {
    document.getElementById("buttonOverlayText").innerHTML = "Checking if Backend alive";
    //check if config.json exists
    if (fs.existsSync(settingspath + "/slateAI/config.json")) {
        conf_json_data = JSON.parse(fs.readFileSync(settingspath + "/slateAI/config.json", 'utf8'));
        //check if it has key "port"
        if ('port' in conf_json_data) {
            port = conf_json_data['port']
            //check if port is not null and not undefined
            if (port != undefined && port != null) {
                console.log("Found saved Port: ", port);
                //check if backend alive on this port 
                backend_alive = await checkIfBackendAlive(port);
                if (backend_alive) {
                    //backend alive on saved port. Use it to connect to backend.
                    document.getElementById("buttonOverlayText").innerHTML = "Connecting to Backend";
                    connectToBackend(port);
                }
                else {
                    //backend not alive on saved port. Check if saved Port is in use.
                    if (await portInUse(port)) {
                        //saved port is in use. find new port.
                        port = await findOpenPort();
                    }
                    //start Backend and connect to it via free port. save Port to file.
                    document.getElementById("buttonOverlayText").innerHTML = "Starting Backend";
                    startBackend(port);
                    saveUsedPort(port);
                    document.getElementById("buttonOverlayText").innerHTML = "Connecting to Backend";
                    connectToBackend(port);
                }
            }
            return
        }
    }
    //Port not saved in file before. Backend not alive. Find new free Port and start Backend and connect to it via free port.
    //save Port to file.
    port = await findOpenPort();
    document.getElementById("buttonOverlayText").innerHTML = "Starting Backend";
    startBackend(port);
    //write used port to file, so we can check next time starting the backend if its already running
    saveUsedPort(port);
    connectToBackend(port);

}

function handleFindClapslButton() {
    orderProjectItemPaths();
}

function onLoaded() {
    csInterface = new CSInterface();
    appName = csInterface.hostEnvironment.appName;
    appVersion = csInterface.hostEnvironment.appVersion;

    APIVersion = csInterface.getCurrentApiVersion();

    caps = csInterface.getHostCapabilities();

    loadJSX();

    updateThemeWithAppSkinInfo(csInterface.hostEnvironment.appSkinInfo);
    //todo delete? - not needed?
    csInterface.addEventListener("com.adobe.csxs.events.WindowVisibilityChanged", function (event) {
        console.log("visibilty changed");
    });

    // Update the color of the panel when the theme color of the product changed.
    csInterface.addEventListener(CSInterface.THEME_COLOR_CHANGED_EVENT, onAppThemeColorChanged);
    // Listen for event sent in response to rendering a sequence.
    csInterface.addEventListener("com.adobe.csxs.events.PProPanelRenderEvent", function (event) {
        alert(event.data);
    });

    csInterface.addEventListener("com.adobe.csxs.events.WorkspaceChanged", function (event) {
        alert("New workspace selected: " + event.data);
    });

    csInterface.addEventListener("com.adobe.ccx.start.handleLicenseBanner", function (event) {
        alert("User chose to go \"Home\", wherever that is...");
    });

    csInterface.addEventListener("ApplicationBeforeQuit", function (event) {
        csInterface.evalScript("$._PPP_.closeLog()");
    });



    // register for messages
    VulcanInterface.addMessageListener(
        VulcanMessage.TYPE_PREFIX + "com.DVA.message.sendtext",
        function (message) {
            var str = VulcanInterface.getPayload(message);
            // You just received the text of every Text layer in the current AE comp.
        }
    );
    //csInterface.evalScript("$._PPP_.getVersionInfo()", myVersionInfoFunction);	
    csInterface.evalScript("$._PPP_.getProjectProxySetting()", myGetProxyFunction);
    csInterface.evalScript("$._PPP_.keepPanelLoaded()");
    csInterface.evalScript("$._PPP_.disableImportWorkspaceWithProjects()");
    csInterface.evalScript("$._PPP_.registerProjectPanelSelectionChangedFxn()"); // Project panel selection changed
    csInterface.evalScript("$._PPP_.registerItemAddedFxn()"); // Item added to project
    csInterface.evalScript("$._PPP_.registerProjectChangedFxn()"); // Project changed
    csInterface.evalScript("$._PPP_.registerSequenceSelectionChangedFxn()"); // Selection within the active sequence changed
    csInterface.evalScript("$._PPP_.registerSequenceActivatedFxn()"); // The active sequence changed
    csInterface.evalScript("$._PPP_.registerActiveSequenceStructureChangedFxn()"); // Clips within the active sequence changed
    csInterface.evalScript("$._PPP_.registerSequenceMessaging()");
    csInterface.evalScript("$._PPP_.registerActiveSequenceChangedFxn()");
    csInterface.evalScript("$._PPP_.confirmPProHostVersion()");
    csInterface.evalScript("$._PPP_.forceLogfilesOn()"); // turn on log files when launching

    // Good idea from our friends at Evolphin; make the ExtendScript locale match the JavaScript locale!
    var prefix = "$._PPP_.setLocale('";
    var locale = csInterface.hostEnvironment.appUILocale;
    var postfix = "');";

    var entireCallWithParams = prefix + locale + postfix;
    csInterface.evalScript(entireCallWithParams);

    initSlateAIExtension();
}


/*PREDEFINED STANDARD EXTENSION CODE, taken from example extension*/

function dragHandler(event) {
    var csInterface = new CSInterface();
    var extPath = csInterface.getSystemPath(SystemPath.EXTENSION);
    var OSVersion = csInterface.getOSInformation();

    /*
    	Note: PPro displays different behavior, depending on where the drag ends (and over which the panel has no control):

    	Project panel?	Import into project.
    	Sequence?		Import into project, add to sequence.
    	Source monitor? Open in source, but do NOT import into project.
    
    */

    if (extPath !== null) {
        extPath = extPath + "/payloads/test.jpg";
        if (OSVersion.indexOf("Windows") >= 0) {
            var sep = "\\\\";
            extPath = extPath.replace(/\//g, sep);
        }
        event.dataTransfer.setData("com.adobe.cep.dnd.file.0", extPath);
        //	event.dataTransfer.setData("com.adobe.cep.dnd.file.N", path);  N = (items to import - 1)
    }
}



function myGetProxyFunction(data) {
    // Updates proxy_display based on current sequence's value.
    var boilerPlate = "Proxies enabled for project: ";
    var proxy_display = document.getElementById("proxies_on");

    if (proxy_display !== null) {
        proxy_display.innerHTML = boilerPlate + data;
    }
}

function mySetProxyFunction(data) {
    var csInterface = new CSInterface();
    csInterface.evalScript("$._PPP_.getActiveSequenceName()", myCallBackFunction);
    csInterface.evalScript("$._PPP_.getProjectProxySetting()", myGetProxyFunction);
}


/**
 * Update the theme with the AppSkinInfo retrieved from the host product.
 */

function updateThemeWithAppSkinInfo(appSkinInfo) {

    //Update the background color of the panel

    var panelBackgroundColor = appSkinInfo.panelBackgroundColor.color;
    document.body.bgColor = toHex(panelBackgroundColor);

    var styleId = "ppstyle";
    var gradientBg = "background-image: -webkit-linear-gradient(top, " + toHex(panelBackgroundColor, 40) + " , " + toHex(panelBackgroundColor, 10) + ");";
    var gradientDisabledBg = "background-image: -webkit-linear-gradient(top, " + toHex(panelBackgroundColor, 15) + " , " + toHex(panelBackgroundColor, 5) + ");";
    var boxShadow = "-webkit-box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.4), 0 1px 1px rgba(0, 0, 0, 0.2);";
    var boxActiveShadow = "-webkit-box-shadow: inset 0 1px 4px rgba(0, 0, 0, 0.6);";

    var isPanelThemeLight = panelBackgroundColor.red > 50; // choose your own sweet spot
    var fontColor, disabledFontColor;
    var borderColor;
    var inputBackgroundColor;
    var gradientHighlightBg;

    if (isPanelThemeLight) {
        fontColor = "#000000;";
        disabledFontColor = "color:" + toHex(panelBackgroundColor, -70) + ";";
        borderColor = "border-color: " + toHex(panelBackgroundColor, -90) + ";";
        inputBackgroundColor = toHex(panelBackgroundColor, 54) + ";";
        gradientHighlightBg = "background-image: -webkit-linear-gradient(top, " + toHex(panelBackgroundColor, -40) + " , " + toHex(panelBackgroundColor, -50) + ");";
    } else {
        fontColor = "#ffffff;";
        disabledFontColor = "color:" + toHex(panelBackgroundColor, 100) + ";";
        borderColor = "border-color: " + toHex(panelBackgroundColor, -45) + ";";
        inputBackgroundColor = toHex(panelBackgroundColor, -20) + ";";
        gradientHighlightBg = "background-image: -webkit-linear-gradient(top, " + toHex(panelBackgroundColor, -20) + " , " + toHex(panelBackgroundColor, -30) + ");";
    }

    //Update the default text style with pp values

    addRule(styleId, ".default", "font-size:" + appSkinInfo.baseFontSize + "px" + "; color:" + fontColor + "; background-color:" + toHex(panelBackgroundColor) + ";");
    addRule(styleId, "button, select, input[type=text], input[type=button], input[type=submit]", borderColor);
    addRule(styleId, "p", "color:" + fontColor + ";");
    addRule(styleId, "h1", "color:" + fontColor + ";");
    addRule(styleId, "h2", "color:" + fontColor + ";");
    addRule(styleId, "button", "font-family: " + appSkinInfo.baseFontFamily + ", Arial, sans-serif;");
    addRule(styleId, "button", "color:" + fontColor + ";");
    addRule(styleId, "button", "font-size:" + (1.2 * appSkinInfo.baseFontSize) + "px;");
    addRule(styleId, "button, select, input[type=button], input[type=submit]", gradientBg);
    addRule(styleId, "button, select, input[type=button], input[type=submit]", boxShadow);
    addRule(styleId, "button:enabled:active, input[type=button]:enabled:active, input[type=submit]:enabled:active", gradientHighlightBg);
    addRule(styleId, "button:enabled:active, input[type=button]:enabled:active, input[type=submit]:enabled:active", boxActiveShadow);
    addRule(styleId, "[disabled]", gradientDisabledBg);
    addRule(styleId, "[disabled]", disabledFontColor);
    addRule(styleId, "input[type=text]", "padding:1px 3px;");
    addRule(styleId, "input[type=text]", "background-color: " + inputBackgroundColor + ";");
    addRule(styleId, "input[type=text]:focus", "background-color: #ffffff;");
    addRule(styleId, "input[type=text]:focus", "color: #000000;");
}

function addRule(stylesheetId, selector, rule) {
    var stylesheet = document.getElementById(stylesheetId);

    if (stylesheet) {
        stylesheet = stylesheet.sheet;
        if (stylesheet.addRule) {
            stylesheet.addRule(selector, rule);
        } else if (stylesheet.insertRule) {
            stylesheet.insertRule(selector + " { " + rule + " }", stylesheet.cssRules.length);
        }
    }
}

function reverseColor(color, delta) {
    return toHex({
        red: Math.abs(255 - color.red),
        green: Math.abs(255 - color.green),
        blue: Math.abs(255 - color.blue)
    }, delta);
}

/**
 * Convert the Color object to string in hexadecimal format;
 */

function toHex(color, delta) {
    function computeValue(value, delta) {
        var computedValue = !isNaN(delta) ? value + delta : value;
        if (computedValue < 0) {
            computedValue = 0;
        } else if (computedValue > 255) {
            computedValue = 255;
        }

        computedValue = Math.round(computedValue).toString(16);
        return computedValue.length == 1 ? "0" + computedValue : computedValue;
    }

    var hex = "";
    if (color) {
        hex = computeValue(color.red, delta) + computeValue(color.green, delta) + computeValue(color.blue, delta);
    }
    return "#" + hex;
}

function onAppThemeColorChanged(event) {
    // Should get a latest HostEnvironment object from application.
    var skinInfo = JSON.parse(window.__adobe_cep__.getHostEnvironment()).appSkinInfo;
    // Gets the style information such as color info from the skinInfo, 
    // and redraw all UI controls of your extension according to the style info.
    updateThemeWithAppSkinInfo(skinInfo);
}

/**
 * Load JSX file into the scripting context of the product. All the jsx files in 
 * folder [ExtensionRoot]/jsx & [ExtensionRoot]/jsx/[AppName] will be loaded.
 */
function loadJSX() {
    var csInterface = new CSInterface();

    // get the appName of the currently used app. For Premiere Pro it's "PPRO"
    var appName = csInterface.hostEnvironment.appName;
    var extensionPath = csInterface.getSystemPath(SystemPath.EXTENSION);

    // load general JSX script independent of appName
    var extensionRootGeneral = extensionPath + "/jsx/";
    csInterface.evalScript("$._ext.evalFiles(\"" + extensionRootGeneral + "\")");

    // load JSX scripts based on appName
    var extensionRootApp = extensionPath + "/jsx/" + appName + "/";
    csInterface.evalScript("$._ext.evalFiles(\"" + extensionRootApp + "\")");
}

function evalScript(script, callback) {
    new CSInterface().evalScript(script, callback);
}

function onClickButton(ppid) {
    var extScript = "$._ext_" + ppid + ".run()";
    evalScript(extScript);
}
