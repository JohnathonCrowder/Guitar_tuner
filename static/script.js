$(document).ready(function() {
    var targetPitch = 0;
    var estimatedPitch = 0;
    var isEstimating = false;
    var intervalId;
    var autoMode = false;

    var $pitchSliderRectangle = $('<div>').attr('id', 'pitch-slider-rectangle').appendTo('#pitch-slider');

    function updatePitchLabels() {
        $('#target-pitch-label').text('Target Pitch: ' + targetPitch.toFixed(2) + ' Hz');
        $('#estimated-pitch-label').text('Estimated Pitch: ' + estimatedPitch.toFixed(2) + ' Hz');
        updatePitchSliderRectangle();
    }

    function updatePitchSlider() {
        var sliderWidth = $('#pitch-slider').width();
        var targetX = sliderWidth / 2;
        var estimatedX = (estimatedPitch - targetPitch + 500) / 1000 * sliderWidth;
    
        $('#pitch-slider').children().not('#pitch-slider-rectangle').remove();
    
        if (isEstimating) {
            if (estimatedX < targetX) {
                $('<div>').css({
                    position: 'absolute',
                    left: estimatedX + 'px',
                    top: 0,
                    width: targetX - estimatedX + 'px',
                    height: '100%',
                    backgroundColor: 'orange'
                }).appendTo('#pitch-slider');
            } else {
                $('<div>').css({
                    position: 'absolute',
                    left: targetX + 'px',
                    top: 0,
                    width: estimatedX - targetX + 'px',
                    height: '100%',
                    backgroundColor: 'orange'
                }).appendTo('#pitch-slider');
            }
        }
    
        $('<div>').css({
            position: 'absolute',
            left: targetX + 'px',
            top: 0,
            width: '2px',
            height: '100%',
            backgroundColor: 'black'
        }).appendTo('#pitch-slider');
    
        updatePitchSliderRectangle();
    }

    function updatePitchSliderRectangle() {
        var pitchDifference = Math.abs(estimatedPitch - targetPitch);
        if (pitchDifference <= 3) {
            $pitchSliderRectangle.css('background-color', 'green');
        } else {
            $pitchSliderRectangle.css('background-color', 'red');
        }
    }

    function findClosestString(estimatedPitch) {
        var closestString = null;
        var minDifference = Infinity;

        $('#string-dropdown option').each(function() {
            var frequency = parseFloat($(this).val());
            var difference = Math.abs(estimatedPitch - frequency);
            if (difference < minDifference) {
                minDifference = difference;
                closestString = $(this);
            }
        });

        return closestString;
    }

    function updateAutoMode() {
        if (autoMode) {
            $('#string-dropdown').prop('disabled', true);
        } else {
            $('#string-dropdown').prop('disabled', false);
        }
    }

    $('#auto-mode-checkbox').change(function() {
        autoMode = $(this).is(':checked');
        updateAutoMode();
    });

    function startEstimation() {
        isEstimating = true;
        $.getJSON('/start_estimation', function(data) {
            intervalId = setInterval(function() {
                $.getJSON('/estimate_pitch', function(data) {
                estimatedPitch = data.estimated_pitch;
                var decibels = data.decibels;
                $('#decibel-rating').text('Decibel Rating: ' + decibels.toFixed(2) + ' dB');
                updatePitchLabels();
                updatePitchSlider();

                if (autoMode) {
                    var closestString = findClosestString(estimatedPitch);
                    if (closestString) {
                        $('#string-dropdown').val(closestString.val());
                        targetPitch = parseFloat(closestString.val());
                        updatePitchLabels();
                        updatePitchSlider();
                    }
                }
            });
        }, 100);
            });
        }

    function stopEstimation() {
        isEstimating = false;
        clearInterval(intervalId);
        $.getJSON('/stop_estimation');
        
        // Clear the Decibel and Estimated Pitch labels
        $('#decibel-rating').text('Decibel Rating: -');
        $('#estimated-pitch-label').text('Estimated Pitch: -');
    }

    $('#string-dropdown').change(function() {
        targetPitch = parseFloat($(this).val());
        updatePitchLabels();
        updatePitchSlider();
    });

    $('#start-button').click(function() {
        startEstimation();
    });

    $('#stop-button').click(function() {
        stopEstimation();
    });

    // Set the target Hz to the first string option on page load
    $('#string-dropdown').trigger('change');

    $('#instrument-dropdown').change(function() {
        var instrument = $(this).val();
        window.location.href = '/?instrument=' + instrument;
    });
});