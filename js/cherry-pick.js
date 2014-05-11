(function($) {

	// init sliders
	var $seasonSlider = $('#seasonSlider'),
		$seasonRange  = $('#seasonRange'),
		$ratingSlider = $('#ratingSlider'),
		$ratingRange  = $('#ratingRange');

	$seasonSlider.slider();
	$ratingSlider.slider({
		range: true,
		min: 1,
		max: 10,
		step: 0.1,
		values: [1, 10],
		slide: function(event, ui) {
			$ratingRange.text( ui.values[0].toFixed(1) + ' - ' + ui.values[1].toFixed(1) );
		},
		change: function(event, ui) {
			filterChart();
		}
	});
	$ratingRange.text( $ratingSlider.slider('values', 0).toFixed(1) + ' - ' + $ratingSlider.slider('values', 1).toFixed(1) );


	// global data
	var shows = {},
		currentShow = null;

	/**
	 * Get color based on index
	 */
	var getColor = (function() {
		var hues = [.6, .2, .05, .1333, .75, 0],
			sats = [.75, 1, .85, .65],
			brts = [.75, .5, .65, .85];
		return function(index) {
        	return 'hsb(' + hues[index%hues.length] + ',' + sats[Math.floor(index/hues.length)] + ',' + brts[Math.floor(index/hues.length)] + ')';
        }
    }());

	/**
	 * Initialize the chart using a series object
	 */
	function makeChart(data) {
		var axis = [], // x
			series = [], // y
			colors = [],
			episode_counter = 0,

			ratingMin = $ratingSlider.slider('values', 0),
			ratingMax = $ratingSlider.slider('values', 1);

		for (var s=0, season; season = data.seasons[s]; s++) {
			var season_axis = [],
				season_series = [];

			for (var e=0, episode; episode = season.episodes[e]; e++, episode_counter++) {
				if (episode['rating'] < ratingMin || episode['rating'] > ratingMax) {
					continue;
				}
				season_axis.push(episode_counter);
				season_series.push(episode['rating']);
			}

			if (season_axis.length > 0) {
				axis.push(season_axis);
				series.push(season_series);
				colors.push( getColor(s) );
			}
		}

		$seasonSlider.slider('destroy');
		$seasonSlider.slider({
			range: true,
			min: 1,
			max: data.seasons.length,
			values: [1, data.seasons.length],
			slide: function(event, ui) {
				$seasonRange.text( ui.values[0] + ' - ' + ui.values[1] );
			},
			change: function(event, ui) {
				filterChart();
			}
		});
		$seasonRange.text( $seasonSlider.slider('values', 0) + ' - ' + $seasonSlider.slider('values', 1) );

		drawChart(axis, series, colors, data);
	}

	/**
	 * Filter the current show on the slider values
	 */
	function filterChart() {
		var data = currentShow,
			axis = [],
			series = [],
			colors = [],
			episode_counter = 0,

			seasonMin = $seasonSlider.slider('values', 0),
			seasonMax = $seasonSlider.slider('values', 1),
			ratingMin = $ratingSlider.slider('values', 0),
			ratingMax = $ratingSlider.slider('values', 1);

		for (var s=0, season; season = data.seasons[s]; s++) {
			var season_axis = [],
				season_series = [];

			for (var e=0, episode; episode = season.episodes[e]; e++, episode_counter++) {
				if (episode['season_number'] < seasonMin || episode['season_number'] > seasonMax) {
					continue;
				}
				if (episode['rating'] < ratingMin || episode['rating'] > ratingMax) {
					continue;
				}
				season_axis.push(episode_counter);
				season_series.push(episode['rating']);
			}

			if (season_axis.length > 0) {
				axis.push(season_axis);
				series.push(season_series);
				colors.push( getColor(s) );
			}
		}

		drawChart(axis, series, colors, data);
	}

	/**
	 * Loop through seasons and get episode by absolute index
	 */
	function getEpisodeByIndex(index, data) {
		data = data || currentShow;

		var counter = 0;

		for (var s=0, season; season = data.seasons[s]; s++) {
			if (index > counter + season.episodes.length - 1) {
				counter += season.episodes.length;
			}
			else {
				return season.episodes[index - counter];
			}
		}
	}

	/**
	 * Draw the chart within the holder element
	 */
	function drawChart(axis, series, colors, data) {
		var $holder = $('#holder').empty();

		if (axis.length < 1) {
			$holder.html('<div id="progress" class="info-box">No data points - adjust the filters</div>');
			return;
		}

		var r = Raphael('holder');

		r.linechart(25, 50, $holder.width() - 50, $holder.height() - 100,
			axis,
			series,
			{
				symbol: 'circle',
				smooth: true,
				axis: '0 0 0 1',
				axisystep: 10,
				colors: colors
			}
		)
		.hover(
			function () {
				var episode = getEpisodeByIndex(this.axis, data);
				var msg = 'S' + episode['season_number'] + 'E' + episode['episode_number'] + '\n' + episode['episode_name'] + '\nRating: ' + this.value;
				this.flag = r.popup(this.x, this.y, msg).insertBefore(this);
			},
			function () {
				this.flag.animate({opacity: 0}, 300, function () { this.remove(); });
			})
		.click(
			function() {
				var episode = getEpisodeByIndex(this.axis, data);
				window.open(episode['episode_url']);
			});
	}

	$('#showSelect')
		/**
		 * Fetch JSON from the server based on option value.
		 * Set the location hash to option value.
		 * Initialize and redraw the chart.
		 */
		.on('change', function() {
			var series_id = $(this).val();
			window.location.hash = series_id;
			if ( typeof shows[series_id] === 'undefined' ) {
				$('#holder').html('<div id="progress" class="loading-box">Loading...</div>');
				$.get('series/' + series_id)
					.success(function(data) {
                        data.seasons.sort(function(a, b) {
                            return a.season_number - b.season_number;
                        });
						currentShow = shows[series_id] = data;
						makeChart(currentShow);
					})
					.fail(function() {
						$('#progress').text('! No data found for selected show !');
					});
			}
			else {
				currentShow = shows[series_id];
				makeChart(shows[series_id]);
			}
		});
		
	$(window)
		.on('resize', function() {
			filterChart();
		})
		.on('hashchange', function() {
			$('#showSelect').find('option[value="' + window.location.hash.slice(1) + '"]').prop('selected', true).end().trigger('change');
		});

	/**
	 * Try to fetch a list of shows from the server and populate the series options list.
	 * Select a show based on location hash or the first option and draw the chart.
	 */
	$.get('series.json')
		.done(function(data) {
			data = data || {};
			var series = data.series || [];
            series.sort(function(a, b) {
                if (a.series_name > b.series_name) { return 1; }
                if (a.series_name < b.series_name) { return -1; }
                return 0;
            });
			if (series.length) {
				$('#showSelect').empty();
				for (var i=0, show; show=series[i]; i++) {
					$('#showSelect').append('<option value="' + show.series_id + '">' + show.series_name + '</option>');
				}
			}
		})
		.always(function() {
			$('#showSelect').find('option[value="' + window.location.hash.slice(1) + '"]').prop('selected', true);
			$('#showSelect').trigger('change');
		});

})(jQuery);
