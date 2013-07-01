/* Contains the helper functions used for PSI and AQI displays
 * PSI functions figure out the colour and descriptor to use
 * AQI functions also include the conversion of AQI from PM2.5
 * concentrations
 *
 */


function Linear(AQIhigh, AQIlow, Conchigh, Conclow, Concentration)
{
	var linear;
	var Conc=parseFloat(Concentration);
	var a;
	a=((Conc-Conclow)/(Conchigh-Conclow))*(AQIhigh-AQIlow)+AQIlow;
	linear=Math.round(a);
	return linear;
}

function AQIPM25(Concentration)
{
	var Conc=parseFloat(Concentration);
	var c;
	var AQI;
	c=(Math.floor(10*Conc))/10;
	if (c>=0 && c<12.1)
	{
		AQI=Linear(50,0,12,0,c);
	}
	else if (c>=12.1 && c<35.5)
	{
		AQI=Linear(100,51,35.4,12.1,c);
	}
	else if (c>=35.5 && c<55.5)
	{
		AQI=Linear(150,101,55.4,35.5,c);
	}
	else if (c>=55.5 && c<150.5)
	{
		AQI=Linear(200,151,150.4,55.5,c);
	}
	else if (c>=150.5 && c<250.5)
	{
		AQI=Linear(300,201,250.4,150.5,c);
	}
	else if (c>=250.5 && c<350.5)
	{
		AQI=Linear(400,301,350.4,250.5,c);
	}
	else if (c>=350.5 && c<500.5)
	{
		AQI=Linear(500,401,500.4,350.5,c);
	}
	else
	{
		AQI="Out of Range";
	}
	return AQI;
}


//set CSS class depending on the PSI value
function setPSIColor( elementName, psiValue ) {
	//clear existing colour
	$(elementName).removeClass("psi-good psi-moderate psi-unhealthy psi-very-unhealthy psi-hazardous");

	if ( psiValue <= 50 )
		psiClass = "psi-good";
	else if ( psiValue <= 100 )
		psiClass = "psi-moderate";
	else if ( psiValue <= 200 )
		psiClass = "psi-unhealthy";
	else if ( psiValue <= 300 )
		psiClass = "psi-very-unhealthy";
	else
		psiClass = "psi-hazardous";

	$(elementName).addClass( psiClass );
}

// get air quality descriptor based on the PSI value	
function getPSIDescriptor( psiValue ) {
	if ( psiValue <= 50 )
		return "Good";
	else if ( psiValue <= 100 )
		return "Moderate";
	else if ( psiValue <= 200 )
		return "Unhealthy";
	else if ( psiValue <= 300 )
		return "Very Unhealthy";
	else
		return "Hazardous";
}


