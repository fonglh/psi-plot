<?php

//get PSI data from database and return JSON object

$dbhost = 'localhost';
$dbname = 'psi_db';
$dbuser = 'psiuser';
$dbpass = 'aNqL6bA5';

/**
 * Set the callback variable to what jQuery sends over
 */
$callback = (string)$_GET[ 'callback' ];
if (!$callback) $callback = 'callback';

$query = (string)$_GET[ 'query' ];

try 
{
	$db = new MongoClient("mongodb://$dbuser:$dbpass@$dbhost/$dbname");
}
catch ( MongoConnectionException $e )
{
	// try no auth
	$db = new MongoClient("mongodb://$dbhost/$dbname");
}

if ( $query === 'psi3hr-all' )
{
	$c_readings = $db -> selectCollection( $dbname, "psi_readings" );

	// get all 3 hour PSI readings
	$cursor = $c_readings->find();
	$cursor->sort( array('timestamp' => 1) );

	$psi_3hr_arr = array();

	while ( $psi_reading = $cursor -> getNext() )
	{
		$psi_3hr_arr[] = array( floatval($psi_reading[ 'timestamp' ] . "000"), intval($psi_reading[ 'psi' ]) );
	}
	$json = json_encode( $psi_3hr_arr );
}
else if ( $query === 'psi3hr-last' )
{
	$c_readings = $db -> selectCollection( $dbname, "psi_readings" );

	// get all 3 hour PSI readings, and limit to the latest one
	$cursor = $c_readings->find();
	$cursor->sort( array('timestamp' => -1) );
	$cursor->limit(1);

	$psi_reading = $cursor -> getNext();
	$psi_3hr_last = array( floatval($psi_reading[ 'timestamp' ] . "000"), intval($psi_reading[ 'psi' ]) );

	$json = json_encode( $psi_3hr_last );
}
else if ( $query === 'psi24hr-all' )
{
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

	foreach ( $psi_24hr_data as &$psi_reading )
	{
		// javascript timestamps are in milliseconds so the values need to be multipled by 1000
		$psi_24hr_arr[] = array( floatval($psi_reading[ 'timestamp' ] . "000"), intval($psi_reading[ 'min' ]), intval($psi_reading[ 'max' ]) );
	}
	$json = json_encode( $psi_24hr_arr );
}
else if ( $query === 'psi24hr-last' )
{
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
	$psi_24hr_last = array_pop( $psi_24hr_data );
	$psi_24hr_last_arr = array( floatval($psi_24hr_last[ 'timestamp' ] . "000"), intval($psi_24hr_last[ 'min' ]), intval($psi_24hr_last[ 'max' ]) );
	$json = json_encode( $psi_24hr_last_arr );
}

header( 'Content-Type: text/javascript' );
echo "$callback($json);";

die;


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


