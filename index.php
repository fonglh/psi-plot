<html>
	<head>
	<?php include_once("analyticstracking.php") ?>
		<title>Singapore PSI Readings</title>
		<script src="//ajax.googleapis.com/ajax/libs/jquery/1.10.1/jquery.min.js"></script>
		<script src="highstock.js"></script>

		<?php

		//get PSI data from database and create data array string

			$dbhost = 'localhost';
			$dbname = 'psi_db';
			$dbuser = 'psiuser';
			$dbpass = 'aNqL6bA5';

			$db = new MongoClient("mongodb://$dbuser:$dbpass@$dbhost/$dbname");
			$c_readings = $db->selectCollection( $dbname, "psi_readings");

			$cursor = $c_readings->find();
			$cursor->sort( array('timestamp' => 1) );

			$data_str = "[";

			while ( $psi_reading = $cursor -> getNext() )
			{
				// javascript timestamps are in milliseconds so the values need to be multipled by 1000
				$data_str .= "[" . $psi_reading[ 'timestamp' ] . "000, " . $psi_reading[ 'psi' ] . "], ";
			}

			//replace final ", " with "]"
			$data_str = substr( $data_str, 0, strlen( $data_str ) - 2 );
			$data_str .= "]"; 
		?>
		<script>
		var chart1;		//globally available
		$(function () {
			chart1 = new Highcharts.StockChart({
				chart: {
					renderTo: 'container'
				},
				rangeSelector: {
					selected: 1
				},
				series: [{
					name: 'PSI Reading',
					data: <?php echo $data_str; ?>
				}]
			});

			Highcharts.setOptions({
				global: {
					useUTC: false
				}
			});

		});

		</script>

	</head>

	<body>
		<div id="container" style="width:80%; height:400px; margin-left:auto; margin-right:auto;"></div>
	</body>
</html>


