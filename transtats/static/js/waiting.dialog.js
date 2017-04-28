/**
 * Module for displaying "Working..." dialog using Bootstrap
 */

var waitingDialog = waitingDialog || (function ($) {
    'use strict';

	// Creating modal dialog's DOM
	var $dialog = $(
		'<div class="modal fade" data-backdrop="static" data-keyboard="false" tabindex="-1" role="dialog" aria-hidden="true" style="top:80%; left:60%; overflow-y:visible;">' +
		'<div class="modal-dialog">' +
		'<div class="modal-content">' +
			'<div class="modal-body">' +
				'<img/>&nbsp;&nbsp;<span class="text-info"></span>' +
			'</div>' +
		'</div></div></div>');

	return {
		/**
		 * Opens dialog
		 * @param message Custom message
		 * @param options Custom options:
		 * 				  options.dialogSize - modal dialog size in px, e.g. 100, 150, 200;
		 * 				  options.imagePath - waiting image path;
		 */
		show: function (message, options) {
			// Assigning defaults
			if (typeof options === 'undefined') {
				options = {};
			}
			if (typeof message === 'undefined') {
				message = 'Working...';
			}
			var settings = $.extend({
				dialogSize: '140',
				imagePath: "/static/img/spin.gif",
				onHide: null // This callback runs after the dialog was hidden
			}, options);

			// Configuring dialog
			$dialog.find('.modal-dialog').css('width', settings.dialogSize + 'px')
			$dialog.find('.text-info').text(message);
			$dialog.find('img').attr('src', settings.imagePath)
			// Adding callbacks
			if (typeof settings.onHide === 'function') {
				$dialog.off('hidden.bs.modal').on('hidden.bs.modal', function (e) {
					settings.onHide.call($dialog);
				});
			}
			// Opening dialog
			$dialog.modal();
		},
		/**
		 * Closes dialog
		 */
		hide: function () {
			$dialog.modal('hide');
		}
	};

})(jQuery);
