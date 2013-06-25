<!DOCTYPE html>
<html>
	<head>
		<title>Singapore PSI Readings</title>
		<meta name="viewport" content="width=device-width, initial-scale=1.0">
		<link href="css/bootstrap.min.css" rel="stylesheet" media="screen">
		<link href="css/bootstrap-responsive.css" rel="stylesheet">
		<script src="//ajax.googleapis.com/ajax/libs/jquery/1.10.1/jquery.min.js"></script>
		<script src="highstock.js"></script>
		<script src="highcharts-more.js"></script>
		<script src="js/bootstrap.min.js"></script>

		<?php

		//get PSI data from database and create data array string

			$dbhost = 'localhost';
			$dbname = 'psi_db';
			$dbuser = 'psiuser';
			$dbpass = 'aNqL6bA5';

			try 
			{
				$db = new MongoClient("mongodb://$dbuser:$dbpass@$dbhost/$dbname");
			}
			catch ( MongoConnectionException $e )
			{
				// try no auth
				$db = new MongoClient("mongodb://$dbhost/$dbname");
			}

			$c_readings = $db -> selectCollection( $dbname, "psi_readings" );

			// get 3 hour PSI readings
			$cursor = $c_readings->find();
			$cursor->sort( array('timestamp' => 1) );

			$psi_3hr_str = "[";

			while ( $psi_reading = $cursor -> getNext() )
			{
				// javascript timestamps are in milliseconds so the values need to be multipled by 1000
				$psi_3hr_str .= "[" . $psi_reading[ 'timestamp' ] . "000, " . $psi_reading[ 'psi' ] . "], ";

				//used later to get the most recent reading
				$curr_3hr_psi = $psi_reading[ 'psi' ];
			}

			//replace final ", " with "]"
			$psi_3hr_str = substr( $psi_3hr_str, 0, strlen( $psi_3hr_str ) - 2 );
			$psi_3hr_str .= "]"; 

			//get 24 hour PSI readings
			$c_readings = $db -> selectCollection( $dbname, "psi_24hr_pm25" );
			$aggregate_ops = array(
								array(
									'$group' => array(
												"_id" => '$timestamp',
												"min" => array('$min'=>'$psi_24'),
												"max" => array('$max'=>'$psi_24')
												)
									),
								array(
									'$project' => array(
													"timestamp" => '$_id',
													'_id' => 0,
													"min" => 1,
													"max" => 1,
													)
									),
								array(
									'$sort' => array(
													'timestamp' => 1
													)
									)
								);
													
			$psi_24hr_data = $c_readings -> aggregate( $aggregate_ops );
			$psi_24hr_data = $psi_24hr_data[ 'result' ];

			$psi_24hr_str = "[";

			foreach ( $psi_24hr_data as &$psi_reading )
			{

				// javascript timestamps are in milliseconds so the values need to be multipled by 1000
				$psi_24hr_str .= "[" . $psi_reading[ 'timestamp' ] . "000, " . $psi_reading[ 'min' ] . ", " . $psi_reading[ 'max' ] . "], ";
			}

			//replace final ", " with "]"
			$psi_24hr_str = substr( $psi_24hr_str, 0, strlen( $psi_24hr_str ) - 2 );
			$psi_24hr_str .= "]"; 

			//get PM2.5 readings
			$aggregate_ops = array(
								array(
									'$group' => array(
												"_id" => '$timestamp',
												"min" => array('$min'=>'$pm25'),
												"max" => array('$max'=>'$pm25')
												)
									),
								array(
									'$project' => array(
													"timestamp" => '$_id',
													'_id' => 0,
													"min" => 1,
													"max" => 1,
													)
									),
								array(
									'$sort' => array(
													'timestamp' => 1
													)
									)
								);
			$pm25_data = $c_readings -> aggregate( $aggregate_ops );
			$pm25_data = $pm25_data[ 'result' ];

			$pm25_str = "[";

			foreach ( $pm25_data as &$psi_reading )
			{

				// javascript timestamps are in milliseconds so the values need to be multipled by 1000
				$pm25_str .= "[" . $psi_reading[ 'timestamp' ] . "000, " . $psi_reading[ 'min' ] . ", " . $psi_reading[ 'max' ] . "], ";

				// used later for current value display
				$curr_pm25 = $psi_reading[ 'min' ] . "-" . $psi_reading[ 'max' ];
			}

			//replace final ", " with "]"
			$pm25_str = substr( $pm25_str, 0, strlen( $pm25_str ) - 2 );
			$pm25_str .= "]"; 

		?>
		<script>
		var chart1;		//globally available
		var chart2;
		$(function () {
			Highcharts.setOptions({
				global: {
					useUTC: false
				}
			});

			chart1 = new Highcharts.StockChart({
				chart: {
					renderTo: 'psi_container',
				},
				rangeSelector: {
					selected: 1
				},

				title: {
					text: 'PSI Readings'
				},

				legend: {
					enabled: true,
					align: 'center',
					verticalAlign: 'bottom',
					borderWidth: 2,
					itemMarginBottom: 10,
				},

				rangeSelector: {
					buttons: [
					{
						type: 'day',
						count: 7,
						text: '7d'
					}, 
					{
						type: 'day',
						count: 3,
						text: '3d'
					},
					{
						type: 'day',
						count: 1,
						text: '1d'
					},
					{
						type: 'all',
						text: 'All'
					}
					],
					selected: 2
				},

				xAxis: {
					ordinal: false
				},

				yAxis: {
					title: {
						text: 'PSI'
					},

					plotBands: [
					{
						from: 0,
						to: 50,
						color: 'rgba(0, 255, 0, 0.7)',
						label: { text: 'Good' }
					},
					{
						from: 51,
						to: 100,
						color: 'rgba(128, 255, 0, 0.7)',
						label: { text: 'Moderate' }
					},
					{
						from: 101,
						to: 200,
						color: 'rgba(255, 255, 0, 0.7)',
						label: { text: 'Unhealthy' }
					},
					{
						from: 201,
						to: 300,
						color: 'rgba(255, 128, 0, 0.7)',
						label: { text: 'Very unhealthy' }
					},
					{
						from: 301,
						to: 500,
						color: 'rgba(255, 0, 0, 0.7)',
						label: { text: 'Hazardous' }
					}
					]

				},

				series: [
				{
					name: 'PSI 3-hr Reading',
					data: <?php echo $psi_3hr_str; ?>
				},
				{
					name: 'PSI 24 hour Range',
					type: 'columnrange',
					data: <?php echo $psi_24hr_str; ?>
				}
				]
			});

			chart2 = new Highcharts.StockChart({
				chart: {
					renderTo: 'pm25_container',
				},
				rangeSelector: {
					selected: 1
				},

				title: {
					text: '24-hr PM2.5 Concentration',
				},

				legend: {
					enabled: true,
					align: 'center',
					verticalAlign: 'bottom',
					borderWidth: 2,
					itemMarginBottom: 10,
				},

				xAxis: {
					ordinal: false
				},

				yAxis: {
					title: {
						text: 'Concentration (&micro;g/m<sup>3</sup>)',
						useHTML: true
					},
				},

				rangeSelector: {
					buttons: [
					{
						type: 'day',
						count: 7,
						text: '7d'
					}, 
					{
						type: 'day',
						count: 3,
						text: '3d'
					},
					{
						type: 'day',
						count: 1,
						text: '1d'
					},
					{
						type: 'all',
						text: 'All'
					}
					],
					selected: 2
				},

				series: [
				{
					name: '24-hr PM2.5 Concentration',
					type: 'columnrange',
					data: <?php echo $pm25_str; ?>
				},
				]
			});


		});

		</script>

	</head>

	<body>
		<div class="container">
			<div class="row">
				<div class="span6">
					<center><h1 style=""><?php echo $curr_3hr_psi; ?></h1></center>
				</div>
				<div class="span6">
					<center><h1 style=""><?php echo $curr_pm25; ?> (&micro;g/m<sup>3</sup>)</h1></center>
				</div>
			</div>
			<div class="row">
				<div class="span6" id="psi_container" style="height:400px;"></div>
				<div class="span6" id="pm25_container" style="height:400px;"></div>
			</div>
		</div>
	</body>
	<?php include_once("analyticstracking.php") ?>
</html>


