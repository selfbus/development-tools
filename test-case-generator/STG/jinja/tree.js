// Copyright (C) 2015-2021 Martin Glueck All rights reserved
// Neugasse 2, A--2244 Spannberg, Austria. martin@mangari.org
// #*** <License> ************************************************************#
// This module is free software; you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation; either version 3 of the License, or
// (at your option) any later version.
//
// This module is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this module. If not, see <http://www.gnu.org/licenses/>.
// #*** </License> ***********************************************************#
//
//++
// Name
//    tree
//
// Purpose
//    Simple tree like handling of a table
//
// Revision Dates
//    13-Feb-2015 (MG) Creation
//--

function tree ($) {
    $.fn.treegrid = function () {
        var hide = function ($elm) {
            $elm.hide ();
            var id = $elm.attr ("id");
            $("tr[data-tree-parent="+id+"]").each (function (i, elm) {
                hide ($(elm));
            });
        };
        var show = function ($elm) {
            $elm.show ();
            var id = $elm.attr ("id");
            $("tr[data-tree-parent="+id+"]").each (function (i, elm) {
                if ($elm.attr ("data-tree-visibility") == "1")
                    show ($(elm));
            });
        };
        // initially hide all non-top-level elements
        $("#parameter-tree tr").not ("[data-tree-parent=0]").show ()
                               .attr ("data-tree-visibility", "1");
        $("#parameter-tree tr[data-tree-parent=0]")
              .attr ("data-tree-visibility", "1");
        $(".tree-node td:first-child").click (function (evt) {
            var $this = $(this);
            var id = $this.parent ().attr ("id");
            var $root = $("#" + id);
            var $children = $("tr[data-tree-parent="+id+"]");
            if ($root.attr ("data-tree-visibility") == "1"){
                $root.attr ("data-tree-visibility", 0);
                $children.each (function (idx, elm) {
                    hide ($(elm));
                });
            } else {
                $root.attr ("data-tree-visibility", 1);
                $children.each (function (idx, elm) {
                    show ($(elm));
                });
            }
        });
        return this;
    }
    function as_hex (value) {
        value = "0000" + value.toString (16).toUpperCase ();
        var l = value.length;
        return value.substring(l, l - 4);
    }

    var data = {};
    function value_changed(pid, value, dep) {
        value = parseInt(value);
        $("#V-" + pid).html (as_hex (value));
        data [pid] = value;
        var $inp  = $("#I-" + pid);
        var mask  = parseInt ($inp.attr ("data-mask"));
        var size  = parseInt ($inp.attr ("data-size"));
        var shift = parseInt ($inp.attr ("data-shift"));
        var addr  = parseInt ($inp.attr ("data-address"));
        value = (value << shift) & mask;
        if ((addr % 2)== 1) {
           addr  -= 1;
           value  = value << 8;
           mask   = mask  << 8;
        }
        var $addr = $("#A-" + addr);
        var  old  = parseInt ($addr.html (), 16);
        value = (old & ~mask) | value;
        $addr.html (as_hex (value));
    };

    function apply_classes ($elm, acls, rcls) {
        $elm.removeClass (rcls).addClass (acls);
        var id = $elm.attr ("id");

        $("[data-tree-parent=" + id + "]").each (function (idx, e){
            apply_classes ($(e), acls, rcls);
        });

    }

    function update_test_tree ($elm) {
        var  id    = $elm.attr ("data-parameter");
        var  value = data [id];
        var  test  = parseInt ($elm.attr ("data-test"));
        var  acls  = (value == test ? "active" : "inactive");
        var  rcls  = (value != test ? "active" : "inactive");
        apply_classes ($elm.parent (), acls, rcls);
    }

	function _set_filter_for_parent ($row) {
	    var pid = $row.attr ("data-tree-parent");
	    var $prow = $("#" + pid);
	    if ($prow.length > 0) {
    	    $prow.find (".filter").prop ("checked", "checked");
	        _set_filter_for_parent ($prow);
	    }
	};

    $(document).ready (function () {
        $("h1").click (function (evt) {
            $("#parameter-tree").treegrid ();
            $(this).css ("color", "green");
        })
        $("#filter").change (function () {
            if ($(this).prop ("checked")) {
                $(".filter").not (":checked").parent ().parent ().hide ();
            } else
                $(".tree-node").show ();
        });
        $("#filter-widget").click (function () {
            $("#filter").prop ("checked", ! $("#filter").prop ("checked")).change ();
        });
        $("#toggle-filter").click (function () {
            var $ncb = $(".filter").not (":checked");
            var $ccb = $(".filter:checked");
            $ncb.prop ("checked", "checked");
            $ccb.prop ("checked", "");
        });
        $("#deselect").click (function () {
            $(".filter").prop ("checked", "");
        });
        $("#add-address-filter").click (function () {
            var addr = $("#address-filter").val ();
            if (addr.length > 0) {
                var $row = $("td[data-address*=" + addr + "]")
                    .parent ();

            	$row.find (".filter")
                    .prop ("checked", "checked");
                $row.each (function (idx, elm) {
                    _set_filter_for_parent ($(elm));
                });
            }
        });
        /*
        $(":input").each (function (idx, inp) {
            var $inp = $(inp);
            var pid  = $inp.attr ("id").slice (2);
            value_changed (pid, $inp.prop ("value"), false);
            $inp.change (function (evt) {
                var $inp  = $(this);
                var pid   = $inp.attr ("id").slice (2);
                var value = $inp.prop ("value");
                value_changed (pid, value, true);
            })
        });
        */
        /*
        $("[data-test]").each (function (idx, elm) {
            update_test_tree ($(elm));
        });
        */
    });
};
tree  (jQuery);
// __END__ tree.js
