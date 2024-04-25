$(document).ready(function() {
    var targetPitch = 0;
    var estimatedPitch = 0;
    var isEstimating = false;
    var intervalId;
    var autoMode = false;

    function updatePitchLabels() {
        $('#target-pitch-label').text('Target Pitch: ' + targetPitch.toFixed(2) + ' Hz');
        $('#estimated-pitch-label').text('Estimated Pitch: ' + estimatedPitch.toFixed(2) + ' Hz');
    }

    function updatePitchSlider() {
        var sliderWidth = $('#pitch-slider').width();
        var targetX = sliderWidth / 2;
        var estimatedX = (estimatedPitch - targetPitch + 500) / 1000 * sliderWidth;

        $('#pitch-slider').empty();

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
    }

    function stopEstimation() {
        isEstimating = false;
        clearInterval(intervalId);
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
});