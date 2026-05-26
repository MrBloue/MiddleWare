// credits to sajjansarkar: http://jsfiddle.net/sajjansarkar/zgcgq8cg/
// and Ana Tudor: https://stackoverflow.com/questions/12813573/position-icons-into-circle
// https://css-tricks.com/snippets/sass/placing-items-circle/

let StickStatus =
{
    xPosition: 0,
    yPosition: 0,
    x: 0,
    y: 0,
    cardinalDirection: "C"
};


var JoyStick = (function(container, parameters, callback)
{
    parameters = parameters || {};
    var title = (typeof parameters.title === "undefined" ? "joystick" : parameters.title),
        width = (typeof parameters.width === "undefined" ? 0 : parameters.width),
        height = (typeof parameters.height === "undefined" ? 0 : parameters.height),
        internalFillColor = (typeof parameters.internalFillColor === "undefined" ? "#0000ff" : parameters.internalFillColor),
        internalLineWidth = (typeof parameters.internalLineWidth === "undefined" ? 2 : parameters.internalLineWidth),
        internalStrokeColor = (typeof parameters.internalStrokeColor === "undefined" ? "#0000ff" : parameters.internalStrokeColor),
        externalLineWidth = (typeof parameters.externalLineWidth === "undefined" ? 2 : parameters.externalLineWidth),
        externalStrokeColor = (typeof parameters.externalStrokeColor ===  "undefined" ? "#0000ff" : parameters.externalStrokeColor),
        autoReturnToCenter = (typeof parameters.autoReturnToCenter === "undefined" ? true : parameters.autoReturnToCenter);

    callback = callback || function(StickStatus) {};

    // Create Canvas element and add it in the Container object
    var objContainer = document.getElementById(container);
    
    // Fixing Unable to preventDefault inside passive event listener due to target being treated as passive in Chrome [Thanks to https://github.com/artisticfox8 for this suggestion]
    objContainer.style.touchAction = "none";

    var canvas = document.createElement("canvas");
    canvas.id = title;
    if(width === 0) { width = objContainer.clientWidth; }
    if(height === 0) { height = objContainer.clientHeight; }
    canvas.width = width;
    canvas.height = height;
    objContainer.appendChild(canvas);
    var context=canvas.getContext("2d");

    var pressed = 0; // Bool - 1=Yes - 0=No
    var circumference = 2 * Math.PI;
    var internalRadius = (canvas.width-((canvas.width/2)+25))/4;
    var maxMoveStick = internalRadius + 5;
    var externalRadius = internalRadius + 30;
    var centerX = canvas.width / 2;
    var centerY = canvas.height / 2;
    var directionHorizontalLimitPos = canvas.width / 10;
    var directionHorizontalLimitNeg = directionHorizontalLimitPos * -1;
    var directionVerticalLimitPos = canvas.height / 10;
    var directionVerticalLimitNeg = directionVerticalLimitPos * -1;
    // Used to save current position of stick
    var movedX=centerX;
    var movedY=centerY;

    // Check if the device support the touch or not
    if("ontouchstart" in document.documentElement)
    {
        canvas.addEventListener("touchstart", onTouchStart, false);
        document.addEventListener("touchmove", onTouchMove, false);
        document.addEventListener("touchend", onTouchEnd, false);
    }
    else
    {
        canvas.addEventListener("mousedown", onMouseDown, false);
        document.addEventListener("mousemove", onMouseMove, false);
        document.addEventListener("mouseup", onMouseUp, false);
    }
    // Draw the object
    drawExternal();
    drawInternal();

    /******************************************************
     * Private methods
     *****************************************************/

    /**
     * @desc Draw the external circle used as reference position
     */
    function drawExternal()
    {
        context.beginPath();
        context.arc(centerX, centerY, externalRadius, 0, circumference, false);
        context.lineWidth = externalLineWidth;
        context.strokeStyle = externalStrokeColor;
        context.stroke();
    }

    /**
     * @desc Draw the internal stick in the current position the user have moved it
     */
    function drawInternal()
    {
       
        context.beginPath();
        if(movedX<internalRadius) { movedX=maxMoveStick; }
        if((movedX+internalRadius) > canvas.width) { movedX = canvas.width-(maxMoveStick); }
        if(movedY<internalRadius) { movedY=maxMoveStick; }
        if((movedY+internalRadius) > canvas.height) { movedY = canvas.height-(maxMoveStick); }
        context.arc(movedX, movedY, internalRadius, 0, circumference, false);
        // create radial gradient
        var grd = context.createRadialGradient(centerX, centerY, 5, centerX, centerY, 200);
        // Light color
        grd.addColorStop(0, internalFillColor);
        // Dark color
        grd.addColorStop(1, internalStrokeColor);
        context.fillStyle = grd;
        context.fill();
        context.lineWidth = internalLineWidth;
        context.strokeStyle = internalStrokeColor;
        context.stroke();
    }

    /**
     * @desc Events for manage touch
     */
    function onTouchStart(event) 
    {
        pressed = 1;
    }

    function onTouchMove(event)
    {
        if(pressed === 1 && event.targetTouches[0].target === canvas)
        {
            movedX = event.targetTouches[0].pageX;
            movedY = event.targetTouches[0].pageY;
            // Manage offset
            if(canvas.offsetParent.tagName.toUpperCase() === "BODY")
            {
                movedX -= canvas.offsetLeft;
                movedY -= canvas.offsetTop;
            }
            else
            {
                movedX -= canvas.offsetParent.offsetLeft;
                movedY -= canvas.offsetParent.offsetTop;
            }
            // Delete canvas
            context.clearRect(0, 0, canvas.width, canvas.height);
            // Redraw object
            drawExternal();
            drawInternal();

            // Set attribute of callback
            StickStatus.xPosition = movedX;
            StickStatus.yPosition = movedY;
            StickStatus.x = (100*((movedX - centerX)/maxMoveStick)).toFixed();
            StickStatus.y = ((100*((movedY - centerY)/maxMoveStick))*-1).toFixed();
            StickStatus.cardinalDirection = getCardinalDirection();
            callback(StickStatus);
        }
    } 

    function onTouchEnd(event) 
    {
        pressed = 0;
        // If required reset position store variable
        if(autoReturnToCenter)
        {
            movedX = centerX;
            movedY = centerY;
        }
        // Delete canvas
        context.clearRect(0, 0, canvas.width, canvas.height);
        // Redraw object
        drawExternal();
        drawInternal();

        // Set attribute of callback
        StickStatus.xPosition = movedX;
        StickStatus.yPosition = movedY;
        StickStatus.x = (100*((movedX - centerX)/maxMoveStick)).toFixed();
        StickStatus.y = ((100*((movedY - centerY)/maxMoveStick))*-1).toFixed();
        StickStatus.cardinalDirection = getCardinalDirection();
        callback(StickStatus);
    }

    /**
     * @desc Events for manage mouse
     */
    function onMouseDown(event) 
    {
        pressed = 1;
    }

    /* To simplify this code there was a new experimental feature here: https://developer.mozilla.org/en-US/docs/Web/API/MouseEvent/offsetX , but it present only in Mouse case not metod presents in Touch case :-( */
    function onMouseMove(event) 
    {
        if(pressed === 1)
        {
            movedX = event.pageX;
            movedY = event.pageY;
            // Manage offset
            if(canvas.offsetParent.tagName.toUpperCase() === "BODY")
            {
                movedX -= canvas.offsetLeft;
                movedY -= canvas.offsetTop;
            }
            else
            {
                movedX -= canvas.offsetParent.offsetLeft;
                movedY -= canvas.offsetParent.offsetTop;
            }
            // Delete canvas
            context.clearRect(0, 0, canvas.width, canvas.height);
            // Redraw object
            drawExternal();
            drawInternal();

            // Set attribute of callback
            StickStatus.xPosition = movedX;
            StickStatus.yPosition = movedY;
            StickStatus.x = (100*((movedX - centerX)/maxMoveStick)).toFixed();
            StickStatus.y = ((100*((movedY - centerY)/maxMoveStick))*-1).toFixed();
            StickStatus.cardinalDirection = getCardinalDirection();
            callback(StickStatus);
        }
    }

    function onMouseUp(event) 
    {
        pressed = 0;
        // If required reset position store variable
        if(autoReturnToCenter)
        {
            movedX = centerX;
            movedY = centerY;
        }
        // Delete canvas
        context.clearRect(0, 0, canvas.width, canvas.height);
        // Redraw object
        drawExternal();
        drawInternal();

        // Set attribute of callback
        StickStatus.xPosition = movedX;
        StickStatus.yPosition = movedY;
        StickStatus.x = (100*((movedX - centerX)/maxMoveStick)).toFixed();
        StickStatus.y = ((100*((movedY - centerY)/maxMoveStick))*-1).toFixed();
        StickStatus.cardinalDirection = getCardinalDirection();
        callback(StickStatus);
    }

    function getCardinalDirection()
    {
        let result = "";
        let orizontal = movedX - centerX;
        let vertical = movedY - centerY;
        
        if(vertical >= directionVerticalLimitNeg && vertical <= directionVerticalLimitPos)
        {
            result = "center";
        }
        if(vertical < directionVerticalLimitNeg)
        {
            result = "up";
        }
        if(vertical > directionVerticalLimitPos)
        {
            result = "down";
        }
        
        if(orizontal < directionHorizontalLimitNeg)
        {
            if(result === "center")
            { 
                result = "left";
            }
            else
            {
                result += "left";
            }
        }
        if(orizontal > directionHorizontalLimitPos)
        {
            if(result === "center")
            { 
                result = "right";
            }
            else
            {
                result += "right";

            }
        }
        
        return result;
    }

    /******************************************************
     * Public methods
     *****************************************************/

    /**
     * @desc The width of canvas
     * @return Number of pixel width 
     */
    this.GetWidth = function () 
    {
        return canvas.width;
    };

    /**
     * @desc The height of canvas
     * @return Number of pixel height
     */
    this.GetHeight = function () 
    {
        return canvas.height;
    };

    /**
     * @desc The X position of the cursor relative to the canvas that contains it and to its dimensions
     * @return Number that indicate relative position
     */
    this.GetPosX = function ()
    {
        return movedX;
    };

    /**
     * @desc The Y position of the cursor relative to the canvas that contains it and to its dimensions
     * @return Number that indicate relative position
     */
    this.GetPosY = function ()
    {
        return movedY;
    };

    /**
     * @desc Normalizzed value of X move of stick
     * @return Integer from -100 to +100
     */
    this.GetX = function ()
    {
        return (100*((movedX - centerX)/maxMoveStick)).toFixed();
    };

    /**
     * @desc Normalizzed value of Y move of stick
     * @return Integer from -100 to +100
     */
    this.GetY = function ()
    {
        return ((100*((movedY - centerY)/maxMoveStick))*-1).toFixed();
    };

    /**
     * @desc Get the direction of the cursor as a string that indicates the cardinal points where this is oriented
     * @return String of cardinal point N, NE, E, SE, S, SW, W, NW and C when it is placed in the center
     */
    let prevDir = "";

    this.GetDir = function() {
        const dir = getCardinalDirection();
        if (dir !== prevDir/* && dir !== 'center'*/) {
            const url_path = "/woz";
            var xhttp = new XMLHttpRequest();
    
            var joystickPayload = { "direction": dir };
            $.ajax({
                type: "POST",
                contentType: "application/json; charset=utf-8",
                url: url_path,
                dataType: "json",
                processData: false,
                data: JSON.stringify(joystickPayload),
    
            }).done(function(data) {
                console.log(data);
            });
        }
        prevDir = dir;
        return dir;
    };
});
//############################################################################################################
///-------------------------------------------------------------------------------------------------------
///-------------------------------------------------------------------------------------------------------
//############################################################################################################


let StickStatusWalk =
{
    xPosition: 0,
    yPosition: 0,
    x: 0,
    y: 0,
    cardinalDirection: "C"
};


var JoyStick2 = (function(container, parameters, callback)
{
    parameters = parameters || {};
    var title = (typeof parameters.title === "undefined" ? "joystick2" : parameters.title),
        width = (typeof parameters.width === "undefined" ? 0 : parameters.width),
        height = (typeof parameters.height === "undefined" ? 0 : parameters.height),
        internalFillColor = (typeof parameters.internalFillColor === "undefined" ? "#0000ff" : parameters.internalFillColor),
        internalLineWidth = (typeof parameters.internalLineWidth === "undefined" ? 2 : parameters.internalLineWidth),
        internalStrokeColor = (typeof parameters.internalStrokeColor === "undefined" ? "#0000ff" : parameters.internalStrokeColor),
        externalLineWidth = (typeof parameters.externalLineWidth === "undefined" ? 2 : parameters.externalLineWidth),
        externalStrokeColor = (typeof parameters.externalStrokeColor ===  "undefined" ? "#0000ff" : parameters.externalStrokeColor),
        autoReturnToCenter = (typeof parameters.autoReturnToCenter === "undefined" ? true : parameters.autoReturnToCenter);

    callback = callback || function(StickStatusWalk) {};

    // Create Canvas element and add it in the Container object
    var objContainer = document.getElementById(container);
    
    // Fixing Unable to preventDefault inside passive event listener due to target being treated as passive in Chrome [Thanks to https://github.com/artisticfox8 for this suggestion]
    objContainer.style.touchAction = "none";

    var canvas = document.createElement("canvas");
    canvas.id = title;
    if(width === 0) { width = objContainer.clientWidth; }
    if(height === 0) { height = objContainer.clientHeight; }
    canvas.width = width;
    canvas.height = height;
    objContainer.appendChild(canvas);
    var context=canvas.getContext("2d");

    var pressed = 0; // Bool - 1=Yes - 0=No
    var circumference = 2 * Math.PI;
    var internalRadius = (canvas.width-((canvas.width/2)+25))/4;
    var maxMoveStick = internalRadius + 5;
    var externalRadius = internalRadius + 30;
    var centerX = canvas.width / 2;
    var centerY = canvas.height / 2;
    var directionHorizontalLimitPos = canvas.width / 10;
    var directionHorizontalLimitNeg = directionHorizontalLimitPos * -1;
    var directionVerticalLimitPos = canvas.height / 10;
    var directionVerticalLimitNeg = directionVerticalLimitPos * -1;
    // Used to save current position of stick
    var movedX=centerX;
    var movedY=centerY;

    // Check if the device support the touch or not
    if("ontouchstart" in document.documentElement)
    {
        canvas.addEventListener("touchstart", onTouchStart, false);
        document.addEventListener("touchmove", onTouchMove, false);
        document.addEventListener("touchend", onTouchEnd, false);
    }
    else
    {
        canvas.addEventListener("mousedown", onMouseDown, false);
        document.addEventListener("mousemove", onMouseMove, false);
        document.addEventListener("mouseup", onMouseUp, false);
    }
    // Draw the object
    drawExternal();
    drawInternal();

    /******************************************************
     * Private methods
     *****************************************************/

    /**
     * @desc Draw the external circle used as reference position
     */
    function drawExternal()
    {
        context.beginPath();
        context.arc(centerX, centerY, externalRadius, 0, circumference, false);
        context.lineWidth = externalLineWidth;
        context.strokeStyle = externalStrokeColor;
        context.stroke();
    }

    /**
     * @desc Draw the internal stick in the current position the user have moved it
     */
    function drawInternal()
    {
       
        context.beginPath();
        if(movedX<internalRadius) { movedX=maxMoveStick; }
        if((movedX+internalRadius) > canvas.width) { movedX = canvas.width-(maxMoveStick); }
        if(movedY<internalRadius) { movedY=maxMoveStick; }
        if((movedY+internalRadius) > canvas.height) { movedY = canvas.height-(maxMoveStick); }
        context.arc(movedX, movedY, internalRadius, 0, circumference, false);
        // create radial gradient
        var grd = context.createRadialGradient(centerX, centerY, 5, centerX, centerY, 200);
        // Light color
        grd.addColorStop(0, internalFillColor);
        // Dark color
        grd.addColorStop(1, internalStrokeColor);
        context.fillStyle = grd;
        context.fill();
        context.lineWidth = internalLineWidth;
        context.strokeStyle = internalStrokeColor;
        context.stroke();
    }

    /**
     * @desc Events for manage touch
     */
    function onTouchStart(event) 
    {
        pressed = 1;
    }

    function onTouchMove(event)
    {
        if(pressed === 1 && event.targetTouches[0].target === canvas)
        {
            movedX = event.targetTouches[0].pageX;
            movedY = event.targetTouches[0].pageY;
            // Manage offset
            if(canvas.offsetParent.tagName.toUpperCase() === "BODY")
            {
                movedX -= canvas.offsetLeft;
                movedY -= canvas.offsetTop;
            }
            else
            {
                movedX -= canvas.offsetParent.offsetLeft;
                movedY -= canvas.offsetParent.offsetTop;
            }
            // Delete canvas
            context.clearRect(0, 0, canvas.width, canvas.height);
            // Redraw object
            drawExternal();
            drawInternal();

            // Set attribute of callback
            StickStatusWalk.xPosition = movedX;
            StickStatusWalk.yPosition = movedY;
            StickStatusWalk.x = (100*((movedX - centerX)/maxMoveStick)).toFixed();
            StickStatusWalk.y = ((100*((movedY - centerY)/maxMoveStick))*-1).toFixed();
            StickStatusWalk.cardinalDirection = getCardinalDirection();
            callback(StickStatusWalk);
        }
    } 

    function onTouchEnd(event) 
    {
        pressed = 0;
        // If required reset position store variable
        if(autoReturnToCenter)
        {
            movedX = centerX;
            movedY = centerY;
        }
        // Delete canvas
        context.clearRect(0, 0, canvas.width, canvas.height);
        // Redraw object
        drawExternal();
        drawInternal();

        // Set attribute of callback
        StickStatusWalk.xPosition = movedX;
        StickStatusWalk.yPosition = movedY;
        StickStatusWalk.x = (100*((movedX - centerX)/maxMoveStick)).toFixed();
        StickStatusWalk.y = ((100*((movedY - centerY)/maxMoveStick))*-1).toFixed();
        StickStatusWalk.cardinalDirection = getCardinalDirection();
        callback(StickStatusWalk);
    }

    /**
     * @desc Events for manage mouse
     */
    function onMouseDown(event) 
    {
        pressed = 1;
    }

    /* To simplify this code there was a new experimental feature here: https://developer.mozilla.org/en-US/docs/Web/API/MouseEvent/offsetX , but it present only in Mouse case not metod presents in Touch case :-( */
    function onMouseMove(event) 
    {
        if(pressed === 1)
        {
            movedX = event.pageX;
            movedY = event.pageY;
            // Manage offset
            if(canvas.offsetParent.tagName.toUpperCase() === "BODY")
            {
                movedX -= canvas.offsetLeft;
                movedY -= canvas.offsetTop;
            }
            else
            {
                movedX -= canvas.offsetParent.offsetLeft;
                movedY -= canvas.offsetParent.offsetTop;
            }
            // Delete canvas
            context.clearRect(0, 0, canvas.width, canvas.height);
            // Redraw object
            drawExternal();
            drawInternal();

            // Set attribute of callback
            StickStatusWalk.xPosition = movedX;
            StickStatusWalk.yPosition = movedY;
            StickStatusWalk.x = (100*((movedX - centerX)/maxMoveStick)).toFixed();
            StickStatusWalk.y = ((100*((movedY - centerY)/maxMoveStick))*-1).toFixed();
            StickStatusWalk.cardinalDirection = getCardinalDirection();
            callback(StickStatusWalk);
        }
    }

    function onMouseUp(event) 
    {
        pressed = 0;
        // If required reset position store variable
        if(autoReturnToCenter)
        {
            movedX = centerX;
            movedY = centerY;
        }
        // Delete canvas
        context.clearRect(0, 0, canvas.width, canvas.height);
        // Redraw object
        drawExternal();
        drawInternal();

        // Set attribute of callback
        StickStatusWalk.xPosition = movedX;
        StickStatusWalk.yPosition = movedY;
        StickStatusWalk.x = (100*((movedX - centerX)/maxMoveStick)).toFixed();
        StickStatusWalk.y = ((100*((movedY - centerY)/maxMoveStick))*-1).toFixed();
        StickStatusWalk.cardinalDirection = getCardinalDirection();
        callback(StickStatusWalk);
    }

    function getCardinalDirection()
    {
        let result = "";
        let orizontal = movedX - centerX;
        let vertical = movedY - centerY;
        
        if(vertical >= directionVerticalLimitNeg && vertical <= directionVerticalLimitPos)
        {
            result = "stop";
        }
        if(vertical < directionVerticalLimitNeg)
        {
            result = "walk_fwd";
        }
        if(vertical > directionVerticalLimitPos)
        {
            result = "walk_back";
        }
        
        if(orizontal < directionHorizontalLimitNeg)
        {
            if(result === "stop")
            { 
                result = "strife_left";
            }
            else
            {
                result = "rotate_left";
            }
        }
        if(orizontal > directionHorizontalLimitPos)
        {
            if(result === "stop")
            { 
                result = "strife_right";
            }
            else
            {
                result = "rotate_right";

            }
        }
        
        return result;
    }

    /******************************************************
     * Public methods
     *****************************************************/

    /**
     * @desc The width of canvas
     * @return Number of pixel width 
     */
    this.GetWidth = function () 
    {
        return canvas.width;
    };

    /**
     * @desc The height of canvas
     * @return Number of pixel height
     */
    this.GetHeight = function () 
    {
        return canvas.height;
    };

    /**
     * @desc The X position of the cursor relative to the canvas that contains it and to its dimensions
     * @return Number that indicate relative position
     */
    this.GetPosX = function ()
    {
        return movedX;
    };

    /**
     * @desc The Y position of the cursor relative to the canvas that contains it and to its dimensions
     * @return Number that indicate relative position
     */
    this.GetPosY = function ()
    {
        return movedY;
    };

    /**
     * @desc Normalizzed value of X move of stick
     * @return Integer from -100 to +100
     */
    this.GetX = function ()
    {
        return (100*((movedX - centerX)/maxMoveStick)).toFixed();
    };

    /**
     * @desc Normalizzed value of Y move of stick
     * @return Integer from -100 to +100
     */
    this.GetY = function ()
    {
        return ((100*((movedY - centerY)/maxMoveStick))*-1).toFixed();
    };

    /**
     * @desc Get the direction of the cursor as a string that indicates the cardinal points where this is oriented
     * @return String of cardinal point N, NE, E, SE, S, SW, W, NW and C when it is placed in the center
     */
   

let prevWalk = "";

this.GetDir = function() {
    const walking = getCardinalDirection();
    if (walking !== prevWalk/* && walking !== 'stop'*/) {
        const url_path = "/woz";
        var xhttp = new XMLHttpRequest();

        var joysticWalkPayload = { "walk": walking };
        $.ajax({
            type: "POST",
            contentType: "application/json; charset=utf-8",
            url: url_path,
            dataType: "json",
            processData: false,
            data: JSON.stringify(joysticWalkPayload),

        }).done(function(data) {
            console.log(data);
        });
    }
    prevWalk = walking;
    return walking;
};
});






// ------------------------------------------------------------------------------------------------------
// ------------------------------------------------------------------------------------------------------

function makeEllipseExact( idWrapper, imageList, ellipseList) {
	var noOfCircles = imageList.length;
	/* equally divide 360 by the no of circles to be drawn */
	var degreeAngle = 360 / noOfCircles;
	/* get handle on the wrapper canvas */
	var wrapper = $("." + idWrapper + "-container");
	/* clear it first */
	wrapper.html("");
	/* initialize angle incrementer variable */
	// var currAngle = delta;
	/* draw each circle at the specified angle */
	for (var i = 0; i < noOfCircles; i++) {
		/* add to the wrapper */
		cordinate = ellipseList[i];
		translationY = cordinate[1];
		translationX = cordinate[0];
		wrapper.append(getGroupDiv(idWrapper + "-" + i, translationX, translationY, imageList[i]));
		/* increment the angle incrementer */
		// currAngle = currAngle + degreeAngle;
	}

}


/*
	Function returns a new DIV with the angles translation using CSS.
	It also applies a random color for fun.
	stole the CSS from :http://stackoverflow.com/questions/12813573/position-icons-into-circle
*/
function getGroupDiv(placeholderId, translationX, translationY, imageInfo) {
	var div = ""
	
	div += "<div id='" + placeholderId + "' class='placeholder' name='" + placeholderId +"' ";
	// div += "style='transform: rotate(" + currAngle + "deg) translate(" + translation + ") rotate(-" + currAngle + "deg);'>"
	div += "style='transform:  translate(" + translationX + "em, " + translationY + "em);'>"	
	if(imageInfo[0].length){
		div += "<img src='" + imageInfo[0] + "' width='100\%' alt='" + imageInfo[1] +"' ";
		div += "onClick='groupButtonClick(\""+ placeholderId +"\")' ondblclick='groupButtonDblClick(\""+ placeholderId +"\")' />"
	}
	else
		div += "<p>" + imageInfo[1] + "</p>";
		
	div += "</div>"
	
	return div
}



function makeCircularCommandList(idCommandsWrapper, commandsList, ellipseList) {
	var wrapper = $("." + idCommandsWrapper + "-container");
	wrapper.html("");
	
	for( var g_id = 0; g_id < commandsList.length; g_id++) {
		var color = commandsList[g_id][0];

		// var noOfCircles = commandsList[g_id][1].length;

		
		for( var c_id = 0; c_id < commandsList[g_id][1].length; c_id++) {
			var id = idCommandsWrapper + "-" + g_id + "-" + c_id
			if (g_id + c_id < commandsList.length) {
				n = g_id + c_id; 
			} else {
				n = g_id + c_id - commandsList.length;
			}

			cordinate = ellipseList[n];
			translationY = cordinate[1];
			translationX = cordinate[0];
			commandsHTML = "";
			commandsHTML += "<div id='" + id + "' class='" + idCommandsWrapper + "-element" + "' name='" + id +"' ";
			commandsHTML += "style='background-color: " + color + "; transform:  translate(" + translationX + "em, " + translationY + "em);' ";
			commandsHTML += "onClick='commandButtonClick("+ g_id + "," + c_id +")' ";
			commandsHTML += ">";
			commandsHTML += commandsList[g_id][1][c_id][0];
			commandsHTML += "</div>";
			wrapper.append(commandsHTML);
			// currAngle = currAngle + degreeAngle;
		}
	}
}




function makeSpinner( idSpinnerWrapper) {
	var wrapper = $("#" + idSpinnerWrapper + "-container");
	wrapper.html("");

	commandsHTML = "<img src='static/images/spinner.gif'/>"
	wrapper.append(commandsHTML);
}


function hideEverything() {	
	for( var i = 0; i < infoList.length; i++) {
		$("#group-info-" + i).show();
		$("#group-text-" + i).show();
	}
	
	var idCommandsWrapper = "commands-list";

	for( var g_id = 0; g_id < commandsList.length; g_id++)
		for( var c_id = 0; c_id < commandsList[g_id][1].length; c_id++) {
			var id = "#" + idCommandsWrapper + "-" + g_id + "-" + c_id;
				$(id).hide();
		}
		
	hideSpinner();
	//$("#spinner-container").hide();
}


function showInfo() {
	var idCommandsWrapper = "commands-list";
	for( var g_id = 0; g_id < commandsList.length; g_id++)
		for( var c_id = 0; c_id < commandsList[g_id][1].length; c_id++) {
			var id = "#" + idCommandsWrapper + "-" + g_id + "-" + c_id;
				$(id).hide();
		}


	var visible = false;
	for( var g_id = 0; g_id < infoList.length; g_id++)
		if($("#group-text-" + g_id).is(":visible")) {
			visible = true;
			break;
		}
	
	if(visible)
		for( var g_id = 0; g_id < infoList.length; g_id++) {
			$("#group-info-" + g_id).hide();
			$("#group-text-" + g_id).hide();
		}
	else
		for( var g_id = 0; g_id < infoList.length; g_id++) {
			$("#group-info-" + g_id).show();
			$("#group-text-" + g_id).show();
		}
}



function groupButtonClick( placeholderId ) {
	var idCommandsWrapper = "commands-list";
	for( var g_id = 0; g_id < commandsList.length; g_id++)
		for( var c_id = 0; c_id < commandsList[g_id][1].length; c_id++) {
			var id = "#" + idCommandsWrapper + "-" + g_id + "-" + c_id;
				$(id).hide();
		}

	var visible = false;
	for( var g_id = 0; g_id < infoList.length; g_id++)
		if($("#group-text-" + g_id).is(":visible")) {
			visible = true;
			break;
		}
	
	var buttonId = placeholderId.split("-")[2];

	if(visible)
		for( var g_id = 0; g_id < infoList.length; g_id++) {
			if(g_id != buttonId) {
				$("#group-info-" + g_id).hide();
				$("#group-text-" + g_id).hide();
			}
		}

	$("#group-info-" + buttonId).toggle();
	$("#group-text-" + buttonId).toggle();
}


function groupButtonDblClick( placeholderId ) {
	for( var g_id = 0; g_id < infoList.length; g_id++) {
		$("#group-info-" + g_id).hide();
		$("#group-text-" + g_id).hide();
	}
	
	var idCommandsWrapper = "commands-list";
	var group_id = placeholderId.split("-")[2];
	for( var g_id = 0; g_id < commandsList.length; g_id++)
		if(g_id != group_id)
			for( var c_id = 0; c_id < commandsList[g_id][1].length; c_id++) {
				var id = "#" + idCommandsWrapper + "-" + g_id + "-" + c_id;
				$(id).hide();
			}

	g_id = group_id;
	for( var c_id = 0; c_id < commandsList[g_id][1].length; c_id++) {
		var id = "#" + idCommandsWrapper + "-" + g_id + "-" + c_id;
			$(id).toggle();
	}

}

// this will send data to flask
var busy = false;
function commandButtonClick( g_id, c_id) {
	if(busy) return;
	command = commandsList[g_id][1][c_id];
	busytime = command[2]*1000;
	// ################################"""""""ici"""""""################################
	// alert(busytime)
	$("#spinner-container").css('visibility', 'visible');
	busy = true;
	setCommandListOpacity("50%");
	setTimeout(hideSpinner, busytime);

	
	//alert(command);
	const url_path = "/woz";
	var xhttp = new XMLHttpRequest();

	// the data sent to flask
	var payload = { "group_id": g_id,
					"control_id": c_id,
					"command": command[1],
					"text": command[0],

					};
					
	$.ajax({
		type: "POST", // HTTP method POST or GET
		contentType: 'application/json; charset=utf-8', //content type
		url: url_path, //Where to make Ajax calls
		dataType:'json', // Data type, HTML, json etc.
		processData: false,
		data: JSON.stringify(payload), 
	}).done(
		function(data) {
			console.log(data);
		}
	);
	
}

function hideSpinner() {
	$("#spinner-container").css('visibility', 'hidden');
	setCommandListOpacity("100%");
	busy = false;
}

function setCommandListOpacity( opacity) {
	var idCommandsWrapper = "commands-list";

	for( var g_id = 0; g_id < commandsList.length; g_id++)
		for( var c_id = 0; c_id < commandsList[g_id][1].length; c_id++) {
			var id = "#" + idCommandsWrapper + "-" + g_id + "-" + c_id;
			$(id).css('opacity', opacity);
		}
}
