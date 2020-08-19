// class to convert the standard JSON representation of a gatenlp
// document into something we need here and methods to access the data.
var gatenlpDocRep = class {
    constructor(jsonstring) {
            this.sep = "║"
            this.sname2types = new Map();
            this.snametype2ids = new Map();
            this.snameid2ann = new Map();
            let bdoc = JSON.parse(jsonstring);
            this.text = bdoc["text"];
            this.features = bdoc["features"];
            if (this.text == null) {
                this.text = "[No proper GATENLP document to show]";
                return;
            }
            let annsets = bdoc["annotation_sets"];
            if (annsets == null) {
                return;
            }
            for (let setname in annsets) {
                // console.log("Processing setname: " + setname)
                let annset = annsets[setname];
                let types4annset = new Set();
                let anns4set = annset["annotations"];
                for (let [idx, element] of anns4set.entries()) {
                    // console.log("adding ann: " + idx + " / " + element)
                    let annid = element["id"].toString();
                    let anntype = element["type"];
                    types4annset.add(anntype);
                    // let snametype = setname + DocRep.sep + anntype;
                    let snametype = setname + this.sep + anntype;
                    // console.log("Created key " + snametype)
                    let ids4type = this.snametype2ids.get(snametype);
                    if (ids4type == null) {
                        //console.log("Adding " + [annid])
                        this.snametype2ids.set(snametype, [annid]);
                        // console.log("keys now " + Array.from(this.snametype2ids.keys()))
                    } else {
                        ids4type.push(annid);
                        // console.log("snametype2ids for " + snametype + " is now " + ids4type)
                    }
                    let snameid = setname + this.sep + annid
                    let ann4snameid = this.snameid2ann.get(snameid);
                    if (ann4snameid == null) {
                        this.snameid2ann.set(snameid, element);
                    } else {
                        // how to handle this odd error?
                    }
                }
                this.sname2types.set(setname, Array.from(types4annset).sort());
            }
        } // constructor

    setnames() {
        return Array.from(this.sname2types.keys()).sort();
    }

    types4setname(setname) {
        // return a sorted list of annotation types for a set name
        return Array.from(this.sname2types.get(setname)); // already sorted!
    }

    annids4snametype(setname, anntype) {
        // return a list of annotation ids for a setname and annotation type
        return this.snametype2ids.get(setname + this.sep + anntype);
    }

    ann4setnameannid(setname, annid) {
        // return the annotation object (map) for a set/id
        return this.snameid2ann.get(setname + this.sep + annid)
    }

    anns4settype(setname, type) {
        //console.log("Getting anns for " + setname + " " + type)
        let annids = this.annids4snametype(setname, type);
        let anns = [];
        for (let annid of annids) {
            anns[anns.length] = this.ann4setnameannid(setname, annid);
        }
        //console.log("Found " + annids + " returning " + anns);
        return anns;
    }

};

function docview_annchosen(rep, ev, setname, anntype) {
        let checked = $(ev.target).prop("checked");
        // this gives us the setname, type and checkbox status of what has been clicked, but for now
        // we always get the complete list of selected types here:
        let seltypes = [];
        let inputs = $(rep.id_chooser).find("input");
        inputs.each(function(index) {
            let inputel = $(inputs.get(index));
            if (inputel.prop("checked")) {
                // seltypes.push(([inputel.attr("data-setname"), inputel.attr("data-anntype")]));
                seltypes[seltypes.length] = [inputel.attr("data-setname"), inputel.attr("data-anntype")]
            }
        });
        rep.chosen = seltypes;
        rep.buildAnns4Offset();
        rep.buildContent();
    }

function docview_annsel(obj, ev, anns) {
        if (anns.length > 1) {
            $(obj.id_popup).empty();
            for (let [setname, annid] of anns) {
                let ann = obj.docrep.ann4setnameannid(setname, annid);
                let feats = ann.features;
                let idpopup = obj.id_popup;
                $("<div class='" + obj.class_selection + "'>" + ann.type + ": id=" + annid + " offsets=" + ann.start + ".." + ann.end + "</div>").on("click", function(x) {
                    docview_showAnn(obj, ann);
                    $(idpopup).hide();
                }).appendTo(obj.id_popup);
            }
            $(obj.id_popup).show();
        } else if (anns.length == 1) {
            let ann = obj.docrep.ann4setnameannid(anns[0][0], anns[0][1]);
            docview_showAnn(obj, ann);
        } else {
            console.error("EMPTY ANNS???");
        }
    }

function docview_showFeatures(obj, features) {
        let tbl = $("<table>").attr("class", obj.idprefix+"featuretable");
        for (let fname in features) {
            let fval = JSON.stringify(features[fname]);
            tbl.append("<tr><td class='" + obj.class_fname + "'>" + fname + "</td><td class='" + obj.class_fvalue + "'>" + fval + "</td></tr>");
        }
        $(obj.id_details).append(tbl);
    }

function docview_showAnn(obj, ann) {
        $(obj.id_details).empty();
        $(obj.id_details).append("<div class='" + obj.id_hdr + "'>Annotation: " + ann.type + " from " + ann.start + " to " + ann.end + "</div>");
        docview_showFeatures(obj, ann.features);
    }

function docview_showDocFeatures(obj, features) {
        $(obj.id_details).empty();
        $(obj.id_details).append("<div class='" + obj.id_hdr + "'>Document features:</div>");
        docview_showFeatures(obj, features);
    }



// class to build the HTML for viewing the converted document
var gatenlpDocView = class {
    constructor(docrep, idprefix="GATENLPID-", config=undefined) {
        // idprefix: the prefix to add to all ids and classes
        this.docrep = docrep;
        this.idprefix = idprefix;
        this.id_text = "#" + idprefix + "text";
        this.id_chooser = "#" + idprefix + "chooser";
        this.id_details = "#" + idprefix + "details";
        this.id_popup = "#" + idprefix + "popup";
        this.id_hdr = "#" + idprefix + "hdr";
        this.id_dochdr = "#" + idprefix + "dochdr";
        this.class_selection = idprefix + "selection";
        this.class_fname = idprefix + "fname";
        this.class_fvalue = idprefix + "fvalue";
        this.class_label = idprefix + "label";
        this.class_input = idprefix + "input";
        this.chosen = [];
        this.anns4offset = undefined;
        // create default config here
        this.config = config;
        this.palettex = [
            // modified from R lib pals: alphabet2
            "#AA6DAA", "#3283FE", "#85660D", "#782AB6", "#565656", "#1C8356", "#16FF32", "#F7E1A0", "#E2E2E2", "#1CBE4F", "#C4451C", "#DEA0FD",
            "#FE00FA", "#325A9B", "#FEAF16", "#F8A19F", "#90AD1C", "#F6222E", "#1CFFCE", "#2ED9FF", "#B10DA1", "#C075A6", "#FC1CBF", "#B00068",
            "#FBE426", "#FA0087",
            // modified from R lib pals: polychrome
            "#5A5156", "#E4E1E3", "#F6222E", "#FE00FA", "#16FF32", "#3283FE", "#FEAF16", "#B00068", "#1CFFCE", "#90AD1C",
            "#2ED9FF", "#DEA0FD", "#AA0DFE", "#F8A19F", "#325A9B", "#C4451C", "#1C8356", "#85660D", "#B10DA1", "#FBE426",
            "#1CBE4F", "#FA0087", "#FC1CBF", "#F7E1A0", "#C075A6", "#782AB6", "#AAF400", "#BDCDFF", "#822E1C", "#B5EFB5",
            "#7ED7D1", "#1C7F93", "#D85FF7", "#683B79", "#66B0FF", "#3B00FB"
        ]

        function hex2rgba(hx) {
            return [
                parseInt(hx.substring(1, 3), 16),
                parseInt(hx.substring(3, 5), 16),
                parseInt(hx.substring(5, 7), 16),
                1.0
            ];
        };
        this.palette = this.palettex.map(hex2rgba)
        this.type2colour = new Map();
    }

    style4color(col) {
        return "background-color: rgba(" + col.join(",") + ");"
    }

    color4types(atypes) {
        // atypes is a list of [setname,type] lists
        let r = 0;
        let g = 0;
        let b = 0;
        let a = 0;
        for (let snametyp of atypes) {
            let typ = snametyp[0] + this.sep + snametyp[1];
            let col = this.type2colour.get(typ);
            r += col[0];
            g += col[1];
            b += col[2];
            a += col[3];
        }
        r = Math.floor(r / atypes.length);
        g = Math.floor(g / atypes.length);
        b = Math.floor(b / atypes.length);
        a = a / atypes.length;
        return [r, g, b, 1.0];
    }

    init() {
        let divcontent = $(this.id_text);
        $(divcontent).empty();
        let text = this.docrep.text;
        let thehtml = $.parseHTML(this.htmlEntities(text));
        $(divcontent).append(thehtml);

        // First of all, create the annotation chooser
        // create a form which contains:
        // for each annotation set create an a tag. followed by a div that contains all the checkbox fields
        let divchooser = $(this.id_chooser);
        $(divchooser).empty();
        let formchooser = $("<form>");
        for (let setname of this.docrep.setnames()) {
            let setname2show = setname;
            // TODO: add number of annotations in the set in parentheses
            if (setname == "") {
                setname2show = "[Default Set]"
            }
            // TODO: make what we show here configurable?
            $(formchooser).append($(document.createElement('div')).attr("class", this.id_hdr).append(setname2show))
            let div4set = document.createElement("div")
            // $(div4set).attr("id", setname);
            $(div4set).attr("style", "margin-bottom: 10px;");
            let colidx = 0
            for (let anntype of this.docrep.types4setname(setname)) {
                //console.log("Addingsss type " + anntype)
                let col = this.palette[colidx];
                this.type2colour.set(setname + this.sep + anntype, col);
                colidx = (colidx + 1) % this.palette.length;
                let lbl = $("<label>").attr({ "style": this.style4color(col), "class": this.class_label });
                let object = this
                let annhandler = function(ev) { docview_annchosen(object, ev, setname, anntype) }
                let inp = $('<input type="checkbox">').attr({ "type": "checkbox", "class": this.class_input, "data-anntype": anntype, "data-setname": setname}).on("click", annhandler)

                $(lbl).append(inp);
                $(lbl).append(anntype);
                // append the number of annotations in this set 
                let n = this.docrep.annids4snametype(setname, anntype).length;
                $(lbl).append(" (" + n + ")");
                $(div4set).append(lbl)
                $(div4set).append($("<br>"))
                $(divchooser).append(formchooser)
            }
            $(formchooser).append(div4set)
        }

        let obj = this;
        let feats = this.docrep["features"];
        docview_showDocFeatures(obj, feats);
        $(this.id_dochdr).text("Document:").on("click", function(ev) { docview_showDocFeatures(obj, feats) });

        this.buildAnns4Offset()
        this.buildContent()
    }

    buildAnns4Offset() {
        //console.log("Running buildAnns4Offset")
        this.anns4offset = new Array(this.docrep.text.length + 1);
        for (let i = 0; i < this.anns4offset.length; i++) {
            this.anns4offset[i] = {
                "snatypes": [],
                "anns": [],
                "offset": i,
            };
        }
        for (let [sname, atype] of this.chosen) {
            //console.log("sname/type: " + sname + "/" + atype);
            // get the annotations 
            let anns = this.docrep.anns4settype(sname, atype);
            for (let ann of anns) {
                // console.log("processing ann: " + ann + " start=" + ann.start + " end=" + ann.end + " type=" + ann.type)
                for (let i = ann.start; i < ann.end; i++) {
                    let have = this.anns4offset[i]
                    let tmp = this.anns4offset[i]["snatypes"];
                    tmp[tmp.length] = [sname, atype];
                    tmp = this.anns4offset[i]["anns"];
                    tmp[tmp.length] = [sname, ann.id];
                    // console.log("entry for start is now " + tmp);
                }
            }
        }
        // now all offsets have a list of annotations 
        // compress the list to only contain the list where it changes 
        let last = this.anns4offset[0]
        for (let i = 1; i < this.anns4offset.length; i++) {
            if (last["snatypes"] == this.anns4offset[i]["snatypes"]) {
                this.anns4offset[i]["snatypes"] = [];
                this.anns4offset[i]["anns"] = [];
            } else {
                last = this.anns4offset[i];
            }
        }
    }

    buildContent() {
        //console.log("Running buildContent");
        // got through all the offsets and check where the annotations change
        // start with the set of annotations in the first offset (empty if undefined) as lastset, calculate color for set
        // go through all subsequent offsets
        // when we find an entry where the annotations change:
        // * get the annotation setname/types 
        // * from the list of setname/types, determine a colour and store it
        // * generate the span from last to here 
        // after the end, generate the last span
        let spans = []
        let last = this.anns4offset[0];
        if (last == undefined) {
            last = { "snatypes": [], "offset": 0 };
        }
        for (let i = 1; i < this.anns4offset.length; i++) {
            let info = this.anns4offset[i];
            if (info != undefined) {
                let txt = this.docrep.text.substring(last["offset"], info["offset"]);
                let span = undefined;
                if (last["snatypes"].length != 0) {
                    //console.log("last-anns:" + last.anns);
                    let col = this.color4types(last.snatypes);
                    let sty = this.style4color(col);
                    span = $('<span>').attr("style", sty);
                    let object = this;
                    let anns = last.anns;
                    let annhandler = function(ev) { docview_annsel(object, ev, anns) }
                    span.on("click", annhandler);
                } else {
                    span = $('<span>');
                }
                span.append($.parseHTML(this.htmlEntities(txt)));
                spans.push(span);
                last = info;
            }
        }
        let txt = this.docrep.text.substring(last["offset"], this.docrep.text.length);
        let span = undefined;
        if (last["snatypes"].length != 0) {
            let col = this.color4types(last.snatypes);
            let sty = this.style4color(col);
            span = $('<span>').attr("style", sty).attr("data-anns", last.snatypes.join(","));
        } else {
            span = $('<span>').attr("data-anns", "");
        }
        span.append($.parseHTML(this.htmlEntities(txt)));
        spans.push(span);
        // Replace the content
        let divcontent = $(this.id_text);
        $(divcontent).empty();
        $(divcontent).append(spans);



    }


    htmlEntities(str) {
        return str.replace(/&/, '&amp;').replace(/</, '&lt;').replace(/>/, '&gt;').replace(/"/, '&quot;').replace(/\n/, "<br>");
    }
};
console.log("Classes defined");
function gatenlp_run(prefix) {
    bdocjson = document.getElementById(prefix+"data").innerHTML;
    new gatenlpDocView(new gatenlpDocRep(bdocjson), prefix).init();
}
console.log("Function defined");
