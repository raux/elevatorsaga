
var createEditor = function() {
    var languageDefinitions = {
        javascript: {
            storageKey: "elevatorCrushCode_v5",
            backupKey: "develevateBackupCode",
            templateId: "#default-elev-implementation",
            mode: "javascript"
        },
        python: {
            storageKey: "elevatorPythonCode_v1",
            backupKey: "elevatorPythonBackupCode",
            templateId: "#default-python-implementation",
            mode: null
        },
        java: {
            storageKey: "elevatorJavaCode_v1",
            backupKey: "elevatorJavaBackupCode",
            templateId: "#default-java-implementation",
            mode: null
        }
    };
    var currentLanguage = "python";

    var cm = CodeMirror.fromTextArea(document.getElementById("code"), {
        lineNumbers: true,
        indentUnit: 4,
        indentWithTabs: false,
        theme: "solarized light",
        mode: "javascript",
        autoCloseBrackets: true,
        extraKeys: {
            // the following Tab key mapping is from http://codemirror.net/doc/manual.html#keymaps
            Tab: function(cm) {
                var spaces = new Array(cm.getOption("indentUnit") + 1).join(" ");
                cm.replaceSelection(spaces);
            }
        }
    });

    // reindent on paste (adapted from https://github.com/ahuth/brackets-paste-and-indent/blob/master/main.js)
    cm.on("change", function(codeMirror, change) {
        if(change.origin !== "paste") {
            return;
        }

        var lineFrom = change.from.line;
        var lineTo = change.from.line + change.text.length;

        function reindentLines(codeMirror, lineFrom, lineTo) {
            codeMirror.operation(function() {
                codeMirror.eachLine(lineFrom, lineTo, function(lineHandle) {
                    codeMirror.indentLine(lineHandle.lineNo(), "smart");
                });
            });
        }

        reindentLines(codeMirror, lineFrom, lineTo);
    });

    var definition = function(language) {
        return languageDefinitions[language];
    };
    var reset = function() {
        cm.setValue($(definition(currentLanguage).templateId).text().trim());
    };
    var loadCode = function(language) {
        var existingCode = localStorage.getItem(definition(language).storageKey);
        cm.setOption("mode", definition(language).mode);
        if(existingCode) {
            cm.setValue(existingCode);
        } else {
            reset();
        }
    };
    var saveCode = function() {
        localStorage.setItem(definition(currentLanguage).storageKey, cm.getValue());
        $("#save_message").text("Code saved " + new Date().toTimeString());
        returnObj.trigger("change");
    };

    loadCode(currentLanguage);

    $("#button_save").click(function() {
        saveCode();
        cm.focus();
    });

    $("#button_reset").click(function() {
        if(confirm("Do you really want to reset this language to its default implementation?")) {
            localStorage.setItem(definition(currentLanguage).backupKey, cm.getValue());
            reset();
        }
        cm.focus();
    });

    $("#button_resetundo").click(function() {
        if(confirm("Do you want to bring back the code as before the last reset?")) {
            cm.setValue(localStorage.getItem(definition(currentLanguage).backupKey) || "");
        }
        cm.focus();
    });

    var returnObj = riot.observable({});
    var autoSaver = _.debounce(saveCode, 1000);
    cm.on("change", function() {
        autoSaver();
    });

    $("#language_selector").change(function() {
        localStorage.setItem(definition(currentLanguage).storageKey, cm.getValue());
        currentLanguage = this.value;
        loadCode(currentLanguage);
        $("#save_message").text("");
        returnObj.trigger("language_changed", currentLanguage);
        cm.focus();
    });

    returnObj.getCodeObj = function() {
        console.log("Getting code...");
        var code = cm.getValue();
        var obj;
        try {
            obj = getCodeObjFromCode(code);
            returnObj.trigger("code_success");
        } catch(e) {
            returnObj.trigger("usercode_error", e);
            return null;
        }
        return obj;
    };
    returnObj.setCode = function(code) {
        cm.setValue(code);
    };
    returnObj.getCode = function() {
        return cm.getValue();
    };
    returnObj.getLanguage = function() {
        return currentLanguage;
    };
    returnObj.setDevTestCode = function() {
        currentLanguage = "javascript";
        $("#language_selector").val(currentLanguage);
        cm.setOption("mode", "javascript");
        cm.setValue($("#devtest-elev-implementation").text().trim());
        returnObj.trigger("language_changed", currentLanguage);
    };

    $("#button_apply").click(function() {
        returnObj.trigger("apply_code");
    });
    return returnObj;
};


var createParamsUrl = function(current, overrides) {
    return "#" + _.map(_.merge(current, overrides), function(val, key) {
        return key + "=" + val;
    }).join(",");
};



$(function() {
    var tsKey = "elevatorTimeScale";
    var editor = createEditor();

    var params = {};

    var $world = $(".innerworld");
    var $stats = $(".statscontainer");
    var $feedback = $(".feedbackcontainer");
    var $challenge = $(".challenge");
    var $codestatus = $(".codestatus");
    var $runtimeOutput = $("#runtime_output");
    var $runtimeStatus = $("#runtime_status");

    var floorTempl = document.getElementById("floor-template").innerHTML.trim();
    var elevatorTempl = document.getElementById("elevator-template").innerHTML.trim();
    var elevatorButtonTempl = document.getElementById("elevatorbutton-template").innerHTML.trim();
    var userTempl = document.getElementById("user-template").innerHTML.trim();
    var challengeTempl = document.getElementById("challenge-template").innerHTML.trim();
    var feedbackTempl = document.getElementById("feedback-template").innerHTML.trim();
    var codeStatusTempl = document.getElementById("codestatus-template").innerHTML.trim();

    var app = riot.observable({});
    app.worldController = createWorldController(1.0 / 60.0);
    app.worldController.on("usercode_error", function(e) {
        console.log("World raised code error", e);
        editor.trigger("usercode_error", e);
    });

    console.log(app.worldController);
    app.worldCreator = createWorldCreator();
    app.world = undefined;
    app.runtimeLanguage = editor.getLanguage();

    app.currentChallengeIndex = 0;

    app.worldController.on("timescale_changed", function() {
        localStorage.setItem(tsKey, app.worldController.timeScale);
        if(app.world) {
            presentChallenge($challenge, challenges[app.currentChallengeIndex], app, app.world, app.worldController, app.currentChallengeIndex + 1, challengeTempl);
        }
    });

    app.startStopOrRestart = function() {
        if(app.runtimeLanguage !== "javascript") {
            return;
        }
        if(app.world.challengeEnded) {
            app.startChallenge(app.currentChallengeIndex);
        } else {
            app.worldController.setPaused(!app.worldController.isPaused);
        }
    };

    app.startChallenge = function(challengeIndex, autoStart) {
        if(typeof app.world !== "undefined") {
            app.world.unWind();
            // TODO: Investigate if memory leaks happen here
        }
        app.currentChallengeIndex = challengeIndex;
        app.world = app.worldCreator.createWorld(challenges[challengeIndex].options);
        window.world = app.world;

        clearAll([$world, $feedback]);
        presentStats($stats, app.world);
        presentChallenge($challenge, challenges[challengeIndex], app, app.world, app.worldController, challengeIndex + 1, challengeTempl);
        presentWorld($world, app.world, floorTempl, elevatorTempl, elevatorButtonTempl, userTempl);

        app.world.on("stats_changed", function() {
            var challengeStatus = challenges[challengeIndex].condition.evaluate(app.world);
            if(challengeStatus !== null) {
                app.world.challengeEnded = true;
                app.worldController.setPaused(true);
                if(challengeStatus) {
                    presentFeedback($feedback, feedbackTempl, app.world, "Success!", "Challenge completed", createParamsUrl(params, { challenge: (challengeIndex + 2)}));
                } else {
                    presentFeedback($feedback, feedbackTempl, app.world, "Challenge failed", "Maybe your program needs an improvement?", "");
                }
            }
        });

        var codeObj;
        if(app.runtimeLanguage === "javascript") {
            codeObj = editor.getCodeObj();
        } else {
            // Keep a paused visualization available while Python or Java runs headlessly.
            codeObj = getCodeObjFromCode($("#default-elev-implementation").text().trim());
            autoStart = false;
        }
        console.log("Starting...");
        app.worldController.start(app.world, codeObj, window.requestAnimationFrame, autoStart);
    };

    app.showRemoteResult = function(result) {
        $codestatus.empty();
        $runtimeOutput.empty().removeClass("success error");
        var output = result.output || "";
        if(!result.ok) {
            $runtimeOutput.addClass("error");
            $("<h5>").text(result.error || "Strategy execution failed.").appendTo($runtimeOutput);
        } else {
            $runtimeOutput.addClass(result.passed ? "success" : "error");
            var stats = result.stats;
            var summary = (result.passed ? "Challenge passed" : "Challenge failed") +
                " — " + stats.transported + " transported, " + stats.moves + " moves, " +
                stats.maxWaitTime.toFixed(1) + "s max wait, " + stats.elapsedTime.toFixed(1) + "s elapsed.";
            $("<h5>").text(summary).appendTo($runtimeOutput);
        }
        if(output) {
            $("<pre>").text(output).appendTo($runtimeOutput);
        }
    };

    app.runRemoteChallenge = function(language) {
        app.worldController.setPaused(true);
        $codestatus.empty();
        $runtimeOutput.removeClass("success error").empty();
        $("<h5>").text("Running " + language + " challenge on the local backend…").appendTo($runtimeOutput);
        $("#button_apply").prop("disabled", true);

        fetch("/api/run", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                language: language,
                code: editor.getCode(),
                challenge: app.currentChallengeIndex + 1
            })
        }).then(function(response) {
            return response.json().then(function(data) {
                if(!response.ok && !data.error) {
                    data.error = "The local execution server returned HTTP " + response.status + ".";
                }
                return data;
            });
        }).then(function(result) {
            app.showRemoteResult(result);
        }).catch(function(error) {
            app.showRemoteResult({
                ok: false,
                error: "Could not reach the multi-language server. Start multilang_server.py and reload. " + error,
                output: ""
            });
        }).then(function() {
            $("#button_apply").prop("disabled", false);
        });
    };

    editor.on("apply_code", function() {
        if(editor.getLanguage() === "javascript") {
            $runtimeOutput.empty().removeClass("success error");
            app.startChallenge(app.currentChallengeIndex, true);
        } else {
            app.runRemoteChallenge(editor.getLanguage());
        }
    });
    editor.on("code_success", function() {
        presentCodeStatus($codestatus, codeStatusTempl);
    });
    editor.on("usercode_error", function(error) {
        presentCodeStatus($codestatus, codeStatusTempl, error);
    });
    editor.on("language_changed", function(language) {
        app.runtimeLanguage = language;
        app.worldController.setPaused(true);
        $codestatus.empty();
        $runtimeOutput.empty().removeClass("success error");
        if(language === "javascript") {
            $runtimeStatus.text("JavaScript runs in the browser with visualization.");
        } else {
            $runtimeStatus.text(language.charAt(0).toUpperCase() + language.slice(1) + " runs headlessly on the local backend when Apply is pressed.");
        }
    });
    editor.on("change", function() {
        $("#fitness_message").addClass("faded");
        var codeStr = editor.getCode();
        // fitnessSuite(codeStr, true, function(results) {
        //     var message = "";
        //     if(!results.error) {
        //         message = "Fitness avg wait times: " + _.map(results, function(r){ return r.options.description + ": " + r.result.avgWaitTime.toPrecision(3) + "s" }).join("&nbsp&nbsp&nbsp");
        //     } else {
        //         message = "Could not compute fitness due to error: " + results.error;
        //     }
        //     $("#fitness_message").html(message).removeClass("faded");
        // });
    });
    editor.trigger("change");

    riot.route(function(path) {
        params = _.reduce(path.split(","), function(result, p) {
            var match = p.match(/(\w+)=(\w+$)/);
            if(match) { result[match[1]] = match[2]; } return result;
        }, {});
        var requestedChallenge = 0;
        var autoStart = false;
        var timeScale = parseFloat(localStorage.getItem(tsKey)) || 2.0;
        _.each(params, function(val, key) {
            if(key === "challenge") {
                requestedChallenge = _.parseInt(val) - 1;
                if(requestedChallenge < 0 || requestedChallenge >= challenges.length) {
                    console.log("Invalid challenge index", requestedChallenge);
                    console.log("Defaulting to first challenge");
                    requestedChallenge = 0;
                }
            } else if(key === "autostart") {
                autoStart = val === "false" ? false : true;
            } else if(key === "timescale") {
                timeScale = parseFloat(val);
            } else if(key === "devtest") {
                editor.setDevTestCode();
            } else if(key === "fullscreen") {
                makeDemoFullscreen();
            }
        });
        app.worldController.setTimeScale(timeScale);
        app.startChallenge(requestedChallenge, autoStart);
    });
});
