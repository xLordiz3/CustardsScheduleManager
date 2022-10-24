class Shift 
{
   constructor()
   {
    self._name;
    self._date;
    self._day;
    self._hours;
    self._time;
   }

   get name()
   {
    return this._name;
   }
   set name(x)
   {
    this._name = x;
   }

   get date()
   {
    return this._date;
   }
   set date(x)
   {
    this._date = x;
   }

   get day()
   {
    return this._day;
   }
   set day(x)
   {
    this._day = x;
   }

   get hours()
   {
    return this._hours;
   }
   set hours(x)
   {
    this._hours = x;
   }

   get time()
   {
    return this._time;
   }
   set time(x)
   {
    this._time = x;
   }
}
var e1;
var s1;
var e2;
var s2;
var typ;
var s1s = document.getElementById('shifts1');
var s2s = document.getElementById('shifts2');
var s1sl = document.getElementById('shifts1l');
var s2sl = document.getElementById('shifts2l');
var type = document.getElementById('type');
var typel = document.getElementById('typel');
var selemp = document.getElementById('selemp');
var selemp2 = document.getElementById('selemp2');
var e2l = document.getElementById('selemp2l');
var sub = document.getElementById('submit');
var subl = document.getElementById('subl');
var type = document.getElementById("type");

e2l.style.display = 'none';
s1sl.style.display = 'none';
typel.style.display = 'none';
s2sl.style.display = 'none';
subl.style.display = 'none';

//First Employee is selected, returns list of their shifts and calls shifts1()
function sel1() 
{
     
    e1 = selemp.value;
    //console.log(e1)
    
    $.ajax({ 
        type: 'POST',
        url: '/switchemp',
        data: { 'emp': e1 },           
        success: function (data) 
        {
            //console.log(data);
            if(e1 != "")
            {
                shifts1(data);
            }
            else
            {
                s1sl.style.display = 'none';
                s1s.options.length = 0;
                s2sl.style.display = 'none';
                s2s.options.length = 0;
                typel.style.display = 'none';
                type.value = "";
                e2l.style.display = 'none';
            }
            
        }
        });
}

// Displays shifts in First Shift section
function shifts1(data)
{
    s1sl.style.display = 'block';
    var shift = new Shift();
    shift.name = e1;
    var opt = document.createElement('option');
    s1s.options.length = 0;
    s1s.appendChild(opt);
    for(s in data)
    {
        
        var keys = Object.keys(data[s]);
        shift.date = data[s]['Date'];
        shift.day = data[s]['Day'];
        shift.hours = data[s]['Hours'];
        shift.time = data[s]['Time'];
        var opt = document.createElement('option');
        opt.value = JSON.stringify(shift);
        opt.innerHTML = shift.name + ", " + shift.date + ", " + shift.day + ", " + shift.time + ", " + shift.hours;
        s1s.appendChild(opt);
    }
}

// Called when a First Shift is selected, displays the Trade Give Away select box
function typeSel()
{
    if(s1s.options.length > 0)
    {
        typel.style.display = 'block';
        typ = type.value;
    }
    else 
    {
        typel.style.display = 'none';
    }

}

// Trade or Give Away is selected, displays Second Employee section
function sel2en()
{
    if(typel.style.display == 'block')
    {
        
        if(type.value == "GIVE" || type.value == "TRADE" || type.value == "TRADESTART" || type.value == "TRADEEND" )
        {
            
            var e2sel = document.querySelector('#selemp2');
            e2sel.value = "";
            var s2sel = document.querySelector('#shifts2');
            s2sel.value = "";
            s2sl.style.display = 'none';
        }
        e2l.style.display = 'block';
    }
    else
    {
        e2l.style.display = 'block';
    }
    typ = type.value;
}

// Second Employee option is selected, returns list of their ships and calls shifts2()
function sel2()
{     
    var selemp = document.getElementById('selemp2') 
    e2 = selemp.value
    $.ajax({ 
        type: 'POST',
        url: '/switchemp',
        data: { 'emp': e2 },           
        success: function (data) 
        {
            if(type.value == "TRADE" || type.value == "TRADESTART" || type.value == "TRADEEND")
            {
                shifts2(data);
                s2sl.style.display = 'block';
            }
            else
            {
                subl.style.display = 'block';
            }
            
        }
        });
}

// Displays shifts in Second Shift section
function shifts2(data)
{
    //console.log(data);
    var shift = new Shift();
    shift.name = e2;
    var opt = document.createElement('option');
    s2s.options.length = 0;
    s2s.appendChild(opt);
    for(s in data)
    {
        var keys = Object.keys(data[s]);
        shift.date = data[s]['Date'];
        shift.day = data[s]['Day'];
        shift.hours = data[s]['Hours'];
        shift.time = data[s]['Time'];
        var opt = document.createElement('option');
        opt.value = JSON.stringify(shift);
        opt.innerHTML = shift.name + ", " + shift.date + ", " + shift.day + ", " + shift.time + ", " + shift.hours;
        s2s.appendChild(opt);
    }
    subl.style.display = 'block';
}

// Change button is pressed, sends to python for SQL updates
function change()
{
    s1 = s1s.value;
    s2 = s2s.value;
    console.log(e1, s1, typ, e2, s2);
    $.ajax({
        type: 'POST',
        url: '/switchconf',
        data: { 's1': s1, 's2': s2, 'type': typ, 'e2': e2},
        success: function (data)
        {
            console.log(data);
            window.location.href = window.location.href;
            //location.reload();
        }
    })
}