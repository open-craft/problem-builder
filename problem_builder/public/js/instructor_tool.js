function InstructorToolBlock(runtime, element) {
    'use strict';
    var $element = $(element);

    // Pagination

    var Result = Backbone.Model.extend({

        initialize: function(attrs, options) {
            _.each(_.zip(Result.properties, options.values), function(pair) {
                this.set(pair[0], pair[1]);
            }, this);
        }

    }, { properties: ['section', 'subsection', 'unit', 'type', 'question', 'answer', 'username'] });

    var Results = Backbone.PageableCollection.extend({

        model: Result,

        state: {
            order: 0
        },

        url: runtime.handlerUrl(element, 'get_result_page'),

        parseState: function(response) {
            return {
                totalRecords: response.num_results,
                pageSize: response.page_size
            };
        },

        parseRecords: function(response) {
            return _.map(response.display_data, function(row) {
                return new Result(null, { values: row });
            });
        },

        fetchOptions: {
            reset: true,
            type: 'POST',
            contentType: 'application/json',
            processData: false,
            beforeSend: function(jqXHR, options) {
                options.data = JSON.stringify(options.data);
            }
        },

        getFirstPage: function() {
            Backbone.PageableCollection.prototype
                .getFirstPage.call(this, this.fetchOptions);
        },

        getPreviousPage: function() {
            Backbone.PageableCollection.prototype
                .getPreviousPage.call(this, this.fetchOptions);
        },

        getNextPage: function() {
            Backbone.PageableCollection.prototype
                .getNextPage.call(this, this.fetchOptions);
        },

        getLastPage: function() {
            Backbone.PageableCollection.prototype
                .getLastPage.call(this, this.fetchOptions);
        },

        getCurrentPage: function() {
            return this.state.currentPage;
        },

        getTotalPages: function() {
            return this.state.totalPages;
        }

    });

    var ResultsView = Backbone.View.extend({

        initialize: function() {
            this.listenTo(this.collection, 'reset', this.render);
        },

        render: function() {
            this._insertRecords();
            this._updateControls();
            this.$('#total-pages').text(this.collection.getTotalPages() || 0);
            $('.data-export-status', $element).empty();
            this.$el.show(700);
            return this;
        },

        _insertRecords: function() {
            var tbody = this.$('tbody');
            tbody.empty();
            this.collection.each(function(result, index) {
                var row = $('<tr>');
                _.each(Result.properties, function(name) {
                    row.append($('<td>').text(result.get(name)));
                });
                tbody.append(row);
            }, this);
            if (this.collection.getTotalPages()) {
                this.$('#current-page').text(this.collection.getCurrentPage());
            } else {
                this.$('#current-page').text(0);
            }
        },

        events: {
            'click #first-page': '_firstPage',
            'click #prev-page': '_prevPage',
            'click #next-page': '_nextPage',
            'click #last-page': '_lastPage'
        },

        _firstPage: function() {
            this.collection.getFirstPage();
            this._updateControls();
        },

        _prevPage: function() {
            if (this.collection.hasPreviousPage()) {
                this.collection.getPreviousPage();
            }
            this._updateControls();
        },

        _nextPage: function() {
            if (this.collection.hasNextPage()) {
                this.collection.getNextPage();
            }
            this._updateControls();
        },

        _lastPage: function() {
            this.collection.getLastPage();
            this._updateControls();
        },

        _updateControls: function() {
            var currentPage = this.collection.getCurrentPage(),
                totalPages = this.collection.getTotalPages() || 0,
                backward = ["#first-page", "#prev-page"],
                forward = ["#next-page", "#last-page"];
                this._enable(backward, currentPage > 1);
                this._enable(forward, currentPage < totalPages);
        },

        _enable: function(controls, condition) {
            _.each(controls, function(control) {
                this.$(control).prop('disabled', !condition);
            }, this);
        }

    });

    var resultsView = new ResultsView({
        collection: new Results([]),
        el: $element.find('#results')
    });

    // Set up gettext in case it isn't available in the client runtime:
    if (typeof gettext == "undefined") {
        window.gettext = function gettext_stub(string) { return string; };
        window.ngettext = function ngettext_stub(strA, strB, n) { return n == 1 ? strA : strB; };
    }
    var $startButton = $element.find('.data-export-start');
    var $cancelButton = $element.find('.data-export-cancel');
    var $downloadButton = $element.find('.data-export-download');
    var $deleteButton = $element.find('.data-export-delete');
    var $blockTypes = $element.find("select[name='block_types']");
    var $rootBlockId = $element.find("select[name='root_block_id']");
    var $username = $element.find("input[name='username']");
    var $matchString = $element.find("input[name='match_string']");
    var $resultTable = $element.find('.data-export-results');

    var status;
    function getStatus() {
        $.ajax({
            type: 'POST',
            url: runtime.handlerUrl(element, 'get_status'),
            data: '{}',
            success: updateStatus,
            dataType: 'json'
        });
    }

    function updateStatus(newStatus) {
        var statusChanged = ! _.isEqual(newStatus, status);
        status = newStatus;
        if (status.export_pending) {
            // Keep polling for status updates when an export is running.
            setTimeout(getStatus, 1000);
        }
        if (statusChanged) updateView();
    }

    function showSpinner() {
        $startButton.prop('disabled', true);
        $cancelButton.prop('disabled', true);
        $downloadButton.prop('disabled', true);
        $deleteButton.prop('disabled', true);
        $('.data-export-status', $element).empty().append(
            $('<i>').addClass('icon fa fa-spinner fa-spin')
        ).css("text-align", "center");
    }

    function hideResults() {
        $resultTable.hide();
    }

    function showResults() {
        if (status.last_export_result) {
            $resultTable.show();
        }
    }

    function handleError(data) {
        // Shim to make the XBlock JsonHandlerError response work with our format.
        status = {'last_export_result': JSON.parse(data.responseText), 'export_pending': false};
        updateView();
    }

    function updateView() {
        var $exportInfo = $('.data-export-info', $element),
            $statusArea = $('.data-export-status', $element), startTime;
        $exportInfo.empty();
        $startButton.toggle(!status.export_pending).prop('disabled', false);
        $cancelButton.toggle(status.export_pending).prop('disabled', false);
        $downloadButton.toggle(Boolean(status.download_url)).prop('disabled', false);
        $deleteButton.toggle(Boolean(status.last_export_result)).prop('disabled', false);
        if (status.last_export_result) {
            if (status.last_export_result.error) {
                $statusArea.append($('<p>').text(
                    _.template(
                        gettext('Data export failed. Reason: <%= error %>'),
                        {'error': status.last_export_result.error}
                    )
                ));
                hideResults();
            } else {
                startTime = new Date(status.last_export_result.start_timestamp * 1000);
                $exportInfo.append($('<p>').text(
                    _.template(
                        ngettext(
                            'Results retrieved on <%= creation_time %> (<%= seconds %> second).',
                            'Results retrieved on <%= creation_time %> (<%= seconds %> seconds).',
                            status.last_export_result.generation_time_s.toFixed(1)
                        ),
                        {
                            'creation_time': startTime.toString(),
                            'seconds': status.last_export_result.generation_time_s.toFixed(1)
                        }
                    )
                ));
                resultsView.collection.getFirstPage();
            }
        } else {
            if (status.export_pending) {
                $statusArea.append($('<p>').text(
                    gettext('The report is currently being generated…')
                ));
            }
        }
    }

    function addHandler($button, handlerName, form_submit) {
        $button.on('click', function() {
            var data;
            if (form_submit) {
                data = {
                    block_types: $blockTypes.val(),
                    root_block_id: $rootBlockId.val(),
                    username: $username.val(),
                    match_string: $matchString.val()
                };
                data = JSON.stringify(data);
            } else {
                data = '{}';
            }
            $.ajax({
                type: 'POST',
                url: runtime.handlerUrl(element, handlerName),
                data: data,
                success: updateStatus,
                error: handleError,
                dataType: 'json'
            });
            showSpinner();
        });
    }

    addHandler($startButton, 'start_export', true);
    addHandler($cancelButton, 'cancel_export');
    addHandler($deleteButton, 'delete_export');

    $startButton.on('click', hideResults);
    $cancelButton.on('click', showResults);
    $deleteButton.on('click', hideResults);

    $downloadButton.on('click', function() {
        window.location.href = status.download_url;
    });

    showSpinner();
    getStatus();

}
