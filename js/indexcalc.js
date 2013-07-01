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

function AQICategory(AQIndex)
{
	var AQI=parseFloat(AQIndex)
	var AQICategory;
	if (AQI<=50)
	{
		AQICategory="Good";
	}
	else if (AQI>50 && AQI<=100)
	{
		AQICategory="Moderate";
	}
	else if (AQI>100 && AQI<=150)
	{
		AQICategory="Unhealthy (Sensitive Groups)";
	}
	else if (AQI>150 && AQI<=200)
	{
		AQICategory="Unhealthy";
	}
	else if (AQI>200 && AQI<=300)
	{
		AQICategory="Very Unhealthy";
	}
	else if (AQI>300 && AQI<=400)
	{
		AQICategory="Hazardous";
	}
	else if (AQI>400 && AQI<=500)
	{
		AQICategory="Hazardous";
	}
	else
	{
		AQICategory="Out of Range";
	}
	return AQICategory;
}

//set css class depending on the AQI value
function setAQIColor( elementName, aqiValue ) {
	//clear existing colour
	$(elementName).removeClass("aqi-good aqi-moderate aqi-sensitive-unhealthy aqi-unhealthy aqi-very-unhealthy aqi-hazardous");

	var AQI=parseFloat(aqiValue)
	var aqiClass;
	if (AQI<=50)
	{
		aqiClass="aqi-good";
	}
	else if (AQI>50 && AQI<=100)
	{
		aqiClass="aqi-moderate";
	}
	else if (AQI>100 && AQI<=150)
	{
		aqiClass="aqi-sensitive-unhealthy";
	}
	else if (AQI>150 && AQI<=200)
	{
		aqiClass="aqi-unhealthy";
	}
	else if (AQI>200 && AQI<=300)
	{
		aqiClass="aqi-very-unhealthy";
	}
	else if (AQI>300 && AQI<=400)
	{
		aqiClass="aqi-hazardous";
	}
	else if (AQI>400 && AQI<=500)
	{
		aqiClass="aqi-hazardous";
	}
	else
	{
		aqiClass="Out of Range";
	}

	$(elementName).addClass( aqiClass );
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


