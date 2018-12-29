
            (function(global){
                var ProblemBuilderXBlockI18N = {
                  init: function() {
                    

(function (globals) {

  var django = globals.django || (globals.django = {});

  
  django.pluralidx = function (n) {
    var v=(n != 1);
    if (typeof(v) == 'boolean') {
      return v ? 1 : 0;
    } else {
      return v;
    }
  };
  

  
  /* gettext library */

  django.catalog = {
    "All": "\u0634\u0645\u0645", 
    "Data export failed. Reason: <%= error %>": "\u064a\u0634\u0641\u0634 \u062b\u0637\u062d\u062e\u0642\u0641 \u0628\u0634\u0647\u0645\u062b\u064a. \u0642\u062b\u0634\u0633\u062e\u0631: <%= error %>", 
    "Results retrieved on <%= creation_time %> (<%= seconds %> second).": [
      "\u0642\u062b\u0633\u0639\u0645\u0641\u0633 \u0642\u062b\u0641\u0642\u0647\u062b\u062f\u062b\u064a \u062e\u0631 <%= creation_time %> (<%= seconds %> \u0633\u062b\u0630\u062e\u0631\u064a).", 
      "\u0642\u062b\u0633\u0639\u0645\u0641\u0633 \u0642\u062b\u0641\u0642\u0647\u062b\u062f\u062b\u064a \u062e\u0631 <%= creation_time %> (<%= seconds %> \u0633\u062b\u0630\u062e\u0631\u064a\u0633)."
    ], 
    "The report is currently being generated\u2026": "\u0641\u0627\u062b \u0642\u062b\u062d\u062e\u0642\u0641 \u0647\u0633 \u0630\u0639\u0642\u0642\u062b\u0631\u0641\u0645\u063a \u0632\u062b\u0647\u0631\u0644 \u0644\u062b\u0631\u062b\u0642\u0634\u0641\u062b\u064a\u2026", 
    "You have used {num_used} of 1 submission.": [
      "\u063a\u062e\u0639 \u0627\u0634\u062f\u062b \u0639\u0633\u062b\u064a {num_used} \u062e\u0628 1 \u0633\u0639\u0632\u0648\u0647\u0633\u0633\u0647\u062e\u0631.", 
      "\u063a\u062e\u0639 \u0627\u0634\u062f\u062b \u0639\u0633\u062b\u064a {num_used} \u062e\u0628 {max_attempts} \u0633\u0639\u0632\u0648\u0647\u0633\u0633\u0647\u062e\u0631\u0633."
    ]
  };

  django.gettext = function (msgid) {
    var value = django.catalog[msgid];
    if (typeof(value) == 'undefined') {
      return msgid;
    } else {
      return (typeof(value) == 'string') ? value : value[0];
    }
  };

  django.ngettext = function (singular, plural, count) {
    var value = django.catalog[singular];
    if (typeof(value) == 'undefined') {
      return (count == 1) ? singular : plural;
    } else {
      return value[django.pluralidx(count)];
    }
  };

  django.gettext_noop = function (msgid) { return msgid; };

  django.pgettext = function (context, msgid) {
    var value = django.gettext(context + '\x04' + msgid);
    if (value.indexOf('\x04') != -1) {
      value = msgid;
    }
    return value;
  };

  django.npgettext = function (context, singular, plural, count) {
    var value = django.ngettext(context + '\x04' + singular, context + '\x04' + plural, count);
    if (value.indexOf('\x04') != -1) {
      value = django.ngettext(singular, plural, count);
    }
    return value;
  };
  

  django.interpolate = function (fmt, obj, named) {
    if (named) {
      return fmt.replace(/%\(\w+\)s/g, function(match){return String(obj[match.slice(2,-2)])});
    } else {
      return fmt.replace(/%s/g, function(match){return String(obj.shift())});
    }
  };


  /* formatting library */

  django.formats = {
    "DATETIME_FORMAT": "N j, Y, P", 
    "DATETIME_INPUT_FORMATS": [
      "%Y-%m-%d %H:%M:%S", 
      "%Y-%m-%d %H:%M:%S.%f", 
      "%Y-%m-%d %H:%M", 
      "%Y-%m-%d", 
      "%m/%d/%Y %H:%M:%S", 
      "%m/%d/%Y %H:%M:%S.%f", 
      "%m/%d/%Y %H:%M", 
      "%m/%d/%Y", 
      "%m/%d/%y %H:%M:%S", 
      "%m/%d/%y %H:%M:%S.%f", 
      "%m/%d/%y %H:%M", 
      "%m/%d/%y"
    ], 
    "DATE_FORMAT": "j F\u060c Y", 
    "DATE_INPUT_FORMATS": [
      "%Y-%m-%d", 
      "%m/%d/%Y", 
      "%m/%d/%y", 
      "%b %d %Y", 
      "%b %d, %Y", 
      "%d %b %Y", 
      "%d %b, %Y", 
      "%B %d %Y", 
      "%B %d, %Y", 
      "%d %B %Y", 
      "%d %B, %Y"
    ], 
    "DECIMAL_SEPARATOR": ",", 
    "FIRST_DAY_OF_WEEK": "0", 
    "MONTH_DAY_FORMAT": "j F", 
    "NUMBER_GROUPING": "0", 
    "SHORT_DATETIME_FORMAT": "m/d/Y P", 
    "SHORT_DATE_FORMAT": "d\u200f/m\u200f/Y", 
    "THOUSAND_SEPARATOR": ".", 
    "TIME_FORMAT": "g:i A", 
    "TIME_INPUT_FORMATS": [
      "%H:%M:%S", 
      "%H:%M:%S.%f", 
      "%H:%M"
    ], 
    "YEAR_MONTH_FORMAT": "F Y"
  };

  django.get_format = function (format_type) {
    var value = django.formats[format_type];
    if (typeof(value) == 'undefined') {
      return format_type;
    } else {
      return value;
    }
  };

  /* add to global namespace */
  globals.pluralidx = django.pluralidx;
  globals.gettext = django.gettext;
  globals.ngettext = django.ngettext;
  globals.gettext_noop = django.gettext_noop;
  globals.pgettext = django.pgettext;
  globals.npgettext = django.npgettext;
  globals.interpolate = django.interpolate;
  globals.get_format = django.get_format;

}(this));


                  }
                };
                ProblemBuilderXBlockI18N.init();
                global.ProblemBuilderXBlockI18N = ProblemBuilderXBlockI18N;
            }(this));
        