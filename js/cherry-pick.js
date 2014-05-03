(function($) {
	$('#seasonSlider').slider();
	$('#ratingSlider').slider({
		range: true,
		min: 1,
		max: 10,
		step: 0.1,
		values: [1, 10],
		slide: function(event, ui) {
			$('#ratingRange').text( ui.values[0].toFixed(1) + ' - ' + ui.values[1].toFixed(1) );
		},
		change: function(event, ui) {
			filterChart();
		}
	});
	$('#ratingRange').text( $('#ratingSlider').slider('values', 0).toFixed(1) + ' - ' + $('#ratingSlider').slider('values', 1).toFixed(1) );


	var shows = {},
		currentShow = null;

	function makeChart(data) {
		var axis = [],
			series = [],
			season_label = -255,
			season_index = -1,
			latest_season = 1;

		for (var i=0; i < data.length; i++) {
			if (season_label > latest_season) {
				latest_season = season_label;
			}
			if (data[i]['episode_rating'] < $('#ratingSlider').slider('values', 0) || data[i]['episode_rating'] > $('#ratingSlider').slider('values', 1)) {
				continue;
			}
			if (data[i]['season_number'] != season_label) {
				season_label = data[i]['season_number'];
				season_index++;
				axis[season_index] = [];
				series[season_index] = [];
			}
			axis[season_index].push(i);
			series[season_index].push(data[i]['episode_rating']);
		};

		$('#seasonSlider').slider('destroy');
		$('#seasonSlider').slider({
			range: true,
			min: 1,
			max: latest_season,
			values: [1, latest_season],
			slide: function(event, ui) {
				$('#seasonRange').text( ui.values[0] + ' - ' + ui.values[1] );
			},
			change: function(event, ui) {
				filterChart();
			}
		});
		$('#seasonRange').text( $('#seasonSlider').slider('values', 0) + ' - ' + $('#seasonSlider').slider('values', 1) );

		drawChart(axis, series, data);
	}

	function filterChart() {
		var data = currentShow,
			axis = [],
			series = [],
			season_label = -255,
			season_index = -1;

		for (var i=0; i < data.length; i++) {
			if (data[i]['season_number'] < $('#seasonSlider').slider('values', 0) || data[i]['season_number'] > $('#seasonSlider').slider('values', 1)) {
				continue;
			}
			if (data[i]['episode_rating'] < $('#ratingSlider').slider('values', 0) || data[i]['episode_rating'] > $('#ratingSlider').slider('values', 1)) {
				continue;
			}
			if (data[i]['season_number'] != season_label) {
				season_label = data[i]['season_number'];
				season_index++;
				axis[season_index] = [];
				series[season_index] = [];
			}
			axis[season_index].push(i);
			series[season_index].push(data[i]['episode_rating']);
		}

		drawChart(axis, series, data);
	}

	function drawChart(axis, series, data) {
		$('#holder').empty();
		var r = Raphael('holder');
		r.linechart(25, 50, $('#holder').width() - 50, $('#holder').height() - 100,
			axis,
			series,
			{ nostroke: false, symbol: 'circle', smooth: true, axis: '0 0 0 1', axisystep: 10 }
		).hover(function () {
			var point = data[this.axis];
			var msg = 'S' + point['season_number'] + 'E' + point['episode_number'] + '\n' + point['episode_name'] + '\nRating: ' + this.value;
			this.flag = r.popup(this.x, this.y, msg).insertBefore(this);
		}, function () {
			this.flag.animate({opacity: 0}, 300, function () { this.remove(); });
		}).click(function() {
			window.open(data[this.axis]['episode_url']);
		});
	}

	$('#showSelect')
		.on('change', function() {
			var title = $(this).val();
			window.location.hash = title;
			if ( typeof shows[title] === 'undefined' ) {
				$('#holder').html('<div id="progress" class="loading-box">Loading...</div>');
				$.get('json/' + title + '.json')
					.success(function(data) {
						shows[title] = data;
						currentShow = shows[title];
						makeChart(shows[title]);
					})
					.fail(function() {
						$('#progress').text('! No data found for selected show !');
					});
			}
			else {
				currentShow = shows[title];
				makeChart(shows[title]);
			}
		});
		
	$(window)
		.on('resize', function() {
			$('#showSelect').trigger('change');
		})
		.on('hashchange', function() {
			$('#showSelect').find('option[value="' + window.location.hash.slice(1) + '"]').prop('selected', true).end().trigger('change');
		});

	$.get('shows', function(data) {
		if (data && data.length > 0) {
			$('#showSelect').empty();
			for (var i=0; i < data.length; i++) {
				$('#showSelect').append('<option value="' + data[i] + '">' + data[i].replace(/_/g, ' ') + '</option>');
			}
			$('#showSelect').find('option[value="' + window.location.hash.slice(1) + '"]').prop('selected', true).end().trigger('change');
		}
	});

})(jQuery);
