
            (function(global){
                var ProblemBuilderXBlockI18N = {
                  init: function() {
                    

(function(globals) {

  var django = globals.django || (globals.django = {});

  
  django.pluralidx = function(n) {
    var v=(n != 1);
    if (typeof(v) == 'boolean') {
      return v ? 1 : 0;
    } else {
      return v;
    }
  };
  

  /* gettext library */

  django.catalog = django.catalog || {};
  
  var newcatalog = {
    "All": "\u00c0ll \u2c60'\u03c3\u044f\u0454\u043c#", 
    "Data export failed. Reason: <%= error %>": "D\u00e4t\u00e4 \u00e9xp\u00f6rt f\u00e4\u00efl\u00e9d. R\u00e9\u00e4s\u00f6n: <%= error %> \u2c60'\u03c3\u044f\u0454\u043c \u03b9\u03c1\u0455\u03c5\u043c \u2202\u03c3\u0142\u03c3\u044f \u0455\u03b9\u0442 \u03b1\u043c\u0454\u0442, \u00a2\u03c3\u03b7\u0455\u0454\u00a2\u0442#", 
    "Results retrieved on <%= creation_time %> (<%= seconds %> second).": [
      "R\u00e9s\u00fclts r\u00e9tr\u00ef\u00e9v\u00e9d \u00f6n <%= creation_time %> (<%= seconds %> s\u00e9\u00e7\u00f6nd). \u2c60'\u03c3\u044f\u0454\u043c \u03b9\u03c1\u0455\u03c5\u043c \u2202\u03c3\u0142\u03c3\u044f \u0455\u03b9\u0442 \u03b1\u043c\u0454\u0442, \u00a2\u03c3\u03b7\u0455\u0454\u00a2\u0442\u0454\u0442\u03c5\u044f#", 
      "R\u00e9s\u00fclts r\u00e9tr\u00ef\u00e9v\u00e9d \u00f6n <%= creation_time %> (<%= seconds %> s\u00e9\u00e7\u00f6nds). \u2c60'\u03c3\u044f\u0454\u043c \u03b9\u03c1\u0455\u03c5\u043c \u2202\u03c3\u0142\u03c3\u044f \u0455\u03b9\u0442 \u03b1\u043c\u0454\u0442, \u00a2\u03c3\u03b7\u0455\u0454\u00a2\u0442\u0454\u0442\u03c5\u044f#"
    ], 
    "The report is currently being generated\u2026": "Th\u00e9 r\u00e9p\u00f6rt \u00efs \u00e7\u00fcrr\u00e9ntl\u00fd \u00df\u00e9\u00efng g\u00e9n\u00e9r\u00e4t\u00e9d\u2026 \u2c60'\u03c3\u044f\u0454\u043c \u03b9\u03c1\u0455\u03c5\u043c \u2202\u03c3\u0142\u03c3\u044f \u0455\u03b9\u0442 \u03b1\u043c\u0454\u0442, \u00a2\u03c3\u03b7\u0455\u0454\u00a2\u0442\u0454\u0442\u03c5\u044f#", 
    "You have used {num_used} of 1 submission.": [
      "\u00dd\u00f6\u00fc h\u00e4v\u00e9 \u00fcs\u00e9d {num_used} \u00f6f 1 s\u00fc\u00dfm\u00efss\u00ef\u00f6n. \u2c60'\u03c3\u044f\u0454\u043c \u03b9\u03c1\u0455\u03c5\u043c \u2202\u03c3\u0142\u03c3\u044f \u0455\u03b9\u0442 \u03b1\u043c\u0454\u0442, \u00a2\u03c3\u03b7\u0455\u0454\u00a2\u0442\u0454\u0442#", 
      "\u00dd\u00f6\u00fc h\u00e4v\u00e9 \u00fcs\u00e9d {num_used} \u00f6f {max_attempts} s\u00fc\u00dfm\u00efss\u00ef\u00f6ns. \u2c60'\u03c3\u044f\u0454\u043c \u03b9\u03c1\u0455\u03c5\u043c \u2202\u03c3\u0142\u03c3\u044f \u0455\u03b9\u0442 \u03b1\u043c\u0454\u0442, \u00a2\u03c3\u03b7\u0455\u0454\u00a2\u0442\u0454\u0442\u03c5#"
    ]
  };
  for (var key in newcatalog) {
    django.catalog[key] = newcatalog[key];
  }
  

  if (!django.jsi18n_initialized) {
    django.gettext = function(msgid) {
      var value = django.catalog[msgid];
      if (typeof(value) == 'undefined') {
        return msgid;
      } else {
        return (typeof(value) == 'string') ? value : value[0];
      }
    };

    django.ngettext = function(singular, plural, count) {
      var value = django.catalog[singular];
      if (typeof(value) == 'undefined') {
        return (count == 1) ? singular : plural;
      } else {
        return value[django.pluralidx(count)];
      }
    };

    django.gettext_noop = function(msgid) { return msgid; };

    django.pgettext = function(context, msgid) {
      var value = django.gettext(context + '\x04' + msgid);
      if (value.indexOf('\x04') != -1) {
        value = msgid;
      }
      return value;
    };

    django.npgettext = function(context, singular, plural, count) {
      var value = django.ngettext(context + '\x04' + singular, context + '\x04' + plural, count);
      if (value.indexOf('\x04') != -1) {
        value = django.ngettext(singular, plural, count);
      }
      return value;
    };

    django.interpolate = function(fmt, obj, named) {
      if (named) {
        return fmt.replace(/%\(\w+\)s/g, function(match){return String(obj[match.slice(2,-2)])});
      } else {
        return fmt.replace(/%s/g, function(match){return String(obj.shift())});
      }
    };


    /* formatting library */

    django.formats = {
    "DATETIME_FORMAT": "j\\-\\a \\d\\e F Y\\, \\j\\e H:i", 
    "DATETIME_INPUT_FORMATS": [
      "%Y-%m-%d %H:%M:%S", 
      "%Y-%m-%d %H:%M", 
      "%Y-%m-%d", 
      "%Y.%m.%d %H:%M:%S", 
      "%Y.%m.%d %H:%M", 
      "%Y.%m.%d", 
      "%d/%m/%Y %H:%M:%S", 
      "%d/%m/%Y %H:%M", 
      "%d/%m/%Y", 
      "%y-%m-%d %H:%M:%S", 
      "%y-%m-%d %H:%M", 
      "%y-%m-%d", 
      "%Y-%m-%d %H:%M:%S.%f"
    ], 
    "DATE_FORMAT": "j\\-\\a \\d\\e F Y", 
    "DATE_INPUT_FORMATS": [
      "%Y-%m-%d", 
      "%y-%m-%d", 
      "%Y %m %d", 
      "%d-a de %b %Y", 
      "%d %b %Y", 
      "%d-a de %B %Y", 
      "%d %B %Y", 
      "%d %m %Y"
    ], 
    "DECIMAL_SEPARATOR": ",", 
    "FIRST_DAY_OF_WEEK": "1", 
    "MONTH_DAY_FORMAT": "j\\-\\a \\d\\e F", 
    "NUMBER_GROUPING": "3", 
    "SHORT_DATETIME_FORMAT": "Y-m-d H:i", 
    "SHORT_DATE_FORMAT": "Y-m-d", 
    "THOUSAND_SEPARATOR": "\u00a0", 
    "TIME_FORMAT": "H:i", 
    "TIME_INPUT_FORMATS": [
      "%H:%M:%S", 
      "%H:%M", 
      "%H:%M:%S.%f"
    ], 
    "YEAR_MONTH_FORMAT": "F \\d\\e Y"
  };

    django.get_format = function(format_type) {
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

    django.jsi18n_initialized = true;
  }

}(this));


                  }
                };
                ProblemBuilderXBlockI18N.init();
                global.ProblemBuilderXBlockI18N = ProblemBuilderXBlockI18N;
            }(this));
        