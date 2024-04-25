$(document).ready(function() {
    var targetPitch = 0;
    var estimatedPitch = 0;
    var intervalId;

    $('#string-dropdown').change(function() {
        targetPitch = parseFloat($(this).val());
        $('#target-pitch-label').text('Target Pitch: ' + targetPitch.toFixed(2) + ' Hz');
    });

    $('#start-button').click(function() {
        $(this).prop('disabled', true);
        $('#stop-button').prop('disabled', false);
        startPitchEstimation();
    });

    $('#stop-button').click(function() {
        $(this).prop('disabled', true);
        $('#start-button').prop('disabled', false);
        stopPitchEstimation();
    });

    $('#auto-mode-checkbox').change(function() {
        if ($(this).is(':checked')) {
            $('#string-dropdown').hide();
            $('#custom-pitch-checkbox').prop('disabled', true);
            $('#custom-pitch-input').hide();
            $('#set-custom-pitch-button').hide();
        } else {
            $('#string-dropdown').show();
            $('#custom-pitch-checkbox').prop('disabled', false);
            if ($('#custom-pitch-checkbox').is(':checked')) {
                $('#custom-pitch-input').show();
                $('#set-custom-pitch-button').show();
            }
        }
    });

    $('#custom-pitch-checkbox').change(function() {
        if ($(this).is(':checked')) {
            $('#custom-pitch-input').show();
            $('#set-custom-pitch-button').show();
        } else {
            $('#custom-pitch-input').hide();
            $('#set-custom-pitch-button').hide();
        }
    });

    $('#set-custom-pitch-button').click(function() {
        var customPitch = parseFloat($('#custom-pitch-input').val());
        if (!isNaN(customPitch)) {
            targetPitch = customPitch;
            $('#target-pitch-label').text('Target Pitch: ' + targetPitch.toFixed(2) + ' Hz');
        }
    });

    function startPitchEstimation() {
        intervalId = setInterval(function() {
            $.getJSON('/estimate_pitch', function(data) {
                estimatedPitch = data.estimated_pitch;
                var decibels = data.decibels;

                if (estimatedPitch === 0) {
                    $('#estimated-pitch-label').text('Estimated Pitch: -');
                    $('#pitch-indicator').css('background-color', 'gray');
                } else {
                    $('#estimated-pitch-label').text('Estimated Pitch: ' + estimatedPitch.toFixed(2) + ' Hz');
                    var pitchDifference = estimatedPitch - targetPitch;

                    if (Math.abs(pitchDifference) <= 10) {
                        $('#pitch-indicator').css('background-color', 'green');
                    } else {
                        $('#pitch-indicator').css('background-color', 'red');
                    }

                    var sliderPosition = (estimatedPitch - targetPitch + 500) / 1000 * 100;
                    $('#pitch-indicator').css('left', sliderPosition + '%');
                }

                $('#decibel-rating').text('Decibel Rating: ' + decibels.toFixed(2) + ' dB');

                if ($('#auto-mode-checkbox').is(':checked')) {
                    findClosestString(estimatedPitch);
                }
            });
        }, 100);
    }

    function stopPitchEstimation() {
        clearInterval(intervalId);
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

        if (closestString) {
            $('#string-dropdown').val(closestString.val());
            targetPitch = parseFloat(closestString.val());
            $('#target-pitch-label').text('Target Pitch: ' + targetPitch.toFixed(2) + ' Hz');
        }
    }
});