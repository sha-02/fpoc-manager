<script>
function collectFortiPoCElements(formID)
{
  // Assign all the global FortiPoC Elements to the form being submitted

  {% if fortipoc_instances %}
    document.getElementById('pocInstance').setAttribute('form', formID);
    document.getElementById('fpocIP').setAttribute('form', formID);
  {% endif %}

  document.getElementById('scpDeploy').setAttribute('form', formID);
  document.getElementById('singlePassDeploy').setAttribute('form', formID);
  document.getElementById('previewOnly').setAttribute('form', formID);
  document.getElementById('targetedFOSversion').setAttribute('form', formID);
}

function selectDeselectFgt(selectDeselectCheckbox)
{
  {% for fgt in fortigates %}
    var ele=document.getElementsByName('{{fgt}}');
    if ( selectDeselectCheckbox.checked ) { ele[0].checked=true; }
    else { ele[0].checked=false; }
  {% endfor %}
}
function selectDeselectLxc(selectDeselectCheckbox)
{
  {% for lxc in lxces %}
    var ele=document.getElementsByName('{{lxc}}');
    if ( selectDeselectCheckbox.checked ) { ele[0].checked=true; }
    else { ele[0].checked=false; }
  {% endfor %}
}
function selectDeselectVyos(selectDeselectCheckbox)
{
  {% for vyos in vyoses %}
    var ele=document.getElementsByName('{{vyos}}');
    if ( selectDeselectCheckbox.checked ) { ele[0].checked=true; }
    else { ele[0].checked=false; }
  {% endfor %}
}

// Enable the tooltips
$(document).ready(function(){
    $('[data-toggle="tooltip"]').tooltip();
});
</script>
